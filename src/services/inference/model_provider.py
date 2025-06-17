import json
import traceback
from typing import Any, AsyncGenerator, Dict, List, Optional

import litellm
from litellm import acompletion, token_counter
from litellm import utils as litellm_utils

from src.services.common.context import Context
from src.services.common.errors import BudgetExceededError, NoAvailableHostError
from src.services.host_api_keys.host_api_key_service import HostApiKeyService
from src.services.inference.dto import DefaultResponseGenerationOptionsDTO, StreamGenerationDTO, TextGenerationDTO, ThinkingContentDTO
from src.services.inference.tools_service import ToolsService
from src.services.usage_tracking.dto import TokenUsageDTO

from src.services.ai_providers.dto import AiProviderModelDTO, ModelHostDTO

from src.config import settings
from src.logging.logging_config import get_logger

# TODO:
# - add prompt caching when supported by the model provider
# - Citations API


class ModelProvider:
    """
    This is an absraction for a model provider.
    Here we can have different implementations for different model providers.
    For now we will just use litellm, but we can add more implementations in the future.
    """

    def __init__(self, context: Context, tools_service: ToolsService, host_api_key_service: HostApiKeyService):
        self.logger = get_logger(__name__)
        self.context = context
        self.tools_service = tools_service
        self.host_api_key_service = host_api_key_service

    async def _get_api_key_for_host(self, host: ModelHostDTO) -> str:

        # Use host.id (UUID) for user API key lookup
        user_key = await self.host_api_key_service.get_user_api_key_for_host(host.id)
        if user_key:
            return user_key

        # Fallback to system API key using host.slug
        return settings.MODEL_HOSTS[host.slug].api_key

    async def _select_available_host(self, model: AiProviderModelDTO) -> ModelHostDTO:
        """Select the first host (by priority) that has an available API key."""
        if not model.hosts:
            raise NoAvailableHostError("No hosts found for model")

        for host in model.hosts:  # Already sorted by priority in DTO
            api_key = await self._get_api_key_for_host(host)
            if api_key:
                return host

        return model.hosts[0]

    # TODO: this might be a bit slow, we should somehow come up with a better way to do this
    def _prepare_messages(self, messages: List[Dict[str, Any]], model_slug: str) -> List[Dict[str, Any]]:
        if litellm_utils.supports_prompt_caching(model_slug):
            messages[0]["cache_control"] = {"type": "ephemeral"}

        # Filter out unsupported file types from messages
        processed_messages = []
        for message in messages:
            if isinstance(message.get("content"), list):
                filtered_content = []
                for content_item in message["content"]:
                    # Keep text content
                    if content_item.get("type") == "text":
                        filtered_content.append(content_item)
                    # Filter image content if vision not supported
                    elif content_item.get("type") == "image_url" and not litellm_utils.supports_vision(model_slug):
                        self.logger.warning(f"Removing image attachment - Model {model_slug} does not support vision")
                    # Filter audio content if audio not supported
                    elif content_item.get("type") == "input_audio" and not litellm_utils.supports_audio_input(model_slug):
                        self.logger.warning(f"Removing audio attachment - Model {model_slug} does not support audio")
                    # Filter PDF content if file uploads not supported
                    elif content_item.get("type") == "file" and not litellm_utils.supports_pdf_input(model_slug):
                        self.logger.warning(f"Removing PDF attachment - Model {model_slug} does not support file uploads")
                    else:
                        filtered_content.append(content_item)

                # Update message with filtered content
                processed_message = message.copy()
                processed_message["content"] = filtered_content
                processed_messages.append(processed_message)
            else:
                processed_messages.append(message)

        return processed_messages

    async def generate_response(
        self,
        model: AiProviderModelDTO,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        **kwargs,
    ) -> Optional[TextGenerationDTO]:
        try:
            selected_host = await self._select_available_host(model)

            api_key = await self._get_api_key_for_host(selected_host)
            model_slug = selected_host.model_slug

            model_name = f"{selected_host.slug}/{model_slug}"

            completion_params = self._get_completion_params(model_name)

            # Initialize accumulated usage tracking
            total_prompt_tokens = 0
            total_completion_tokens = 0
            total_tokens = 0

            response = await acompletion(
                model=model_name,
                messages=self._prepare_messages(messages, model_slug),
                api_key=api_key,
                **completion_params,
                **kwargs,
            )

            # Accumulate usage from initial response
            if response.usage:
                total_prompt_tokens += response.usage.prompt_tokens
                total_completion_tokens += response.usage.completion_tokens
                total_tokens += response.usage.total_tokens

            # Handle tool calls if present
            response_message = response.choices[0].message
            if response_message.tool_calls:
                await self._handle_tool_calls(tool_calls=response_message.tool_calls, messages=messages, assistant_content=response_message.content or "")

                # Continue making API calls until no more tool calls
                while True:
                    response = await acompletion(
                        model=model_name,
                        messages=messages,
                        api_key=api_key,
                        **completion_params,
                        **kwargs,
                    )

                    # Accumulate usage from each tool call iteration
                    if response.usage:
                        total_prompt_tokens += response.usage.prompt_tokens
                        total_completion_tokens += response.usage.completion_tokens
                        total_tokens += response.usage.total_tokens

                    response_message = response.choices[0].message
                    if response_message.tool_calls:
                        await self._handle_tool_calls(tool_calls=response_message.tool_calls, messages=messages, assistant_content=response_message.content or "")
                    else:
                        break

            return TextGenerationDTO(
                text=response.choices[0].message.content,
                usage=TokenUsageDTO(
                    prompt_tokens=total_prompt_tokens,
                    completion_tokens=total_completion_tokens,
                    total_tokens=total_tokens,
                ),
            )
        except litellm.BudgetExceededError as e:
            raise BudgetExceededError(e)
        except Exception as e:
            self.logger.error(f"Error in generate_response: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise e

    # TODO: try to extract common processing tool method
    async def generate_response_stream(
        self,
        model: AiProviderModelDTO,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamGenerationDTO, None]:
        """Stream response from the model with error handling.

        This returns an AsyncGenerator that will either yield StreamGenerationResponse objects
        or, in case of an error, yield a single Exception object and then stop.
        """
        try:
            selected_host = await self._select_available_host(model)

            api_key = await self._get_api_key_for_host(selected_host)
            model_slug = selected_host.model_slug

            model_name = f"{selected_host.slug}/{model_slug}"
            completion_params = self._get_completion_params(model_name)

            current_messages = self._prepare_messages(messages.copy(), model_slug)

            # Initialize accumulated usage tracking
            total_prompt_tokens = 0
            total_completion_tokens = 0
            total_tokens = 0

            while True:  # Loop for handling tool calls
                response = await acompletion(
                    model=model_name,
                    messages=current_messages,
                    stream=True,
                    api_key=api_key,
                    stream_options={"include_usage": True},
                    **completion_params,
                    **kwargs,
                )

                # Buffer to accumulate the complete response
                complete_response_content = ""
                tool_calls = None

                async for chunk in response:
                    if (chunk.choices and chunk.choices[0].delta and 
                        hasattr(chunk.choices[0].delta, "reasoning_content") and 
                        chunk.choices[0].delta.reasoning_content):
                        yield StreamGenerationDTO(
                            text=None, 
                            usage=None, 
                            reasoning=chunk.choices[0].delta.reasoning_content
                        )

                    if (chunk.choices and chunk.choices[0].delta and 
                        hasattr(chunk.choices[0].delta, "thinking_blocks") and 
                        chunk.choices[0].delta.thinking_blocks):
                        yield StreamGenerationDTO(
                            text=None,
                            usage=None,
                            thinking=[
                                ThinkingContentDTO(
                                    type=block.get("type"),
                                    thinking=block.get("thinking"),
                                    signature=block.get("signature")
                                )
                                for block in chunk.choices[0].delta.thinking_blocks
                            ]
                        )

                    # Handle regular text content after reasoning
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        chunk_text = chunk.choices[0].delta.content
                        complete_response_content += chunk_text
                        yield StreamGenerationDTO(text=chunk_text, usage=None)
                    
                    # Handle usage tracking
                    elif hasattr(chunk, "usage") and chunk.usage:
                        # Accumulate usage from this iteration
                        total_prompt_tokens += chunk.usage.prompt_tokens
                        total_completion_tokens += chunk.usage.completion_tokens
                        total_tokens += chunk.usage.total_tokens

                    # Capture tool calls from the response
                    if chunk.choices and chunk.choices[0].delta and hasattr(chunk.choices[0].delta, "tool_calls") and chunk.choices[0].delta.tool_calls:
                        tool_calls = chunk.choices[0].delta.tool_calls

                # Check if there are tool calls to process
                if tool_calls:
                    await self._handle_tool_calls(tool_calls=tool_calls, messages=current_messages, assistant_content=complete_response_content)
                    # Continue the loop to make another call with updated messages
                    continue
                else:
                    # No tool calls, send final accumulated usage and break
                    if total_prompt_tokens > 0 or total_completion_tokens > 0:
                        final_usage = TokenUsageDTO(
                            prompt_tokens=total_prompt_tokens,
                            completion_tokens=total_completion_tokens,
                            total_tokens=total_tokens,
                        )
                        yield StreamGenerationDTO(text="", usage=final_usage)
                    break

        except litellm.BudgetExceededError as e:
            raise BudgetExceededError(e)
        except Exception as e:
            self.logger.error(f"Error in generate_response_stream: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise e

    async def count_tokens(
        self,
        model: AiProviderModelDTO,
        messages: List[Dict[str, Any]],
    ) -> int:
        selected_host = await self._select_available_host(model)

        model_slug = selected_host.model_slug
        return token_counter(model=f"{selected_host.slug}/{model_slug}", messages=messages)

    async def cost_per_token(self, model: AiProviderModelDTO, usage: TokenUsageDTO) -> float:
        prompt_tokens_cost_usd = model.price_input_token * usage.prompt_tokens
        completion_tokens_cost_usd = model.price_output_token * usage.completion_tokens
        return prompt_tokens_cost_usd + completion_tokens_cost_usd

    def _get_completion_params(self, model: str) -> Dict[str, Any]:
        response = {
            "drop_params": True,
        }

        skip_tools = []
        if litellm.supports_web_search(model=model):
            skip_tools.append("web_search")
            response["web_search_options"] = {
                "search_context_size": settings.WEB_SEARCH_CONTEXT_SIZE,
            }

        function_schemas = self.tools_service.get_function_schemas(skip_tools=skip_tools)

        if litellm.supports_function_calling(model=model) and function_schemas and len(function_schemas) > 0:
            response["tool_choice"] = "auto"
            response["tools"] = function_schemas

        if litellm.supports_reasoning(model=model):
            response["reasoning_effort"] = settings.REASONING_EFFORT

        return response

    async def _handle_tool_calls(
        self,
        tool_calls: List[Any],
        messages: List[Dict[str, Any]],
        assistant_content: str = "",
    ) -> None:
        if not tool_calls:
            return

        # Add the assistant's response to messages
        messages.append({"role": "assistant", "content": assistant_content, "tool_calls": tool_calls})

        # Process each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name

            try:
                function_args = json.loads(tool_call.function.arguments)
                result = self.tools_service.execute_function(function_name, function_args)

                # Add the function response to messages
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result,
                    }
                )
            except Exception as e:
                error_message = f"Error processing tool call: {str(e)}"
                self.logger.error(error_message)
                self.logger.error(traceback.format_exc())

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"error": error_message}),
                    }
                )

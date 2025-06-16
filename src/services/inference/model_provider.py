import json
import traceback
from typing import Any, AsyncGenerator, Dict, List, Optional, Callable

import litellm
from litellm import OpenAIWebSearchOptions, acompletion, token_counter
from litellm import utils as litellm_utils

from src.services.common.context import Context
from src.services.common.errors import BudgetExceededError
from src.services.inference.dto import DefaultResponseGenerationOptionsDTO, StreamGenerationDTO, TextGenerationDTO
from src.services.usage_tracking.dto import TokenUsageDTO
from src.services.inference.tools_service import ToolsService

from src.services.ai_providers.dto import AiProviderModelDTO

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

    def __init__(self, context: Context, tools_service: ToolsService):
        self.logger = get_logger(__name__)
        self.context = context
        self.tools_service = tools_service

    # TODO: this might be a bit slow, we should somehow come up with a better way to do this
    def _prepare_messages(self, messages: List[Dict[str, Any]], model: AiProviderModelDTO) -> List[Dict[str, Any]]:
        if litellm_utils.supports_prompt_caching(model.slug):
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
                    elif content_item.get("type") == "image_url" and not litellm_utils.supports_vision(model.slug):
                        self.logger.warning(f"Removing image attachment - Model {model.slug} does not support vision")
                    # Filter audio content if audio not supported
                    elif content_item.get("type") == "input_audio" and not litellm_utils.supports_audio_input(model.slug):
                        self.logger.warning(f"Removing audio attachment - Model {model.slug} does not support audio")
                    # Filter PDF content if file uploads not supported
                    elif content_item.get("type") == "file" and not litellm_utils.supports_pdf_input(model.slug):
                        self.logger.warning(f"Removing PDF attachment - Model {model.slug} does not support file uploads")
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
            model_name = f"{model.hosts[0].slug}/{model.slug}"
            completion_params = self._get_completion_params(model_name)
            response = await acompletion(
                model=model_name,
                messages=self._prepare_messages(messages, model),
                api_key=settings.MODEL_HOSTS[model.hosts[0].slug].api_key,
                **completion_params,
                **kwargs,
            )

            process_tool_calls = await self._process_tool_calls(response=response, messages=messages)

            while process_tool_calls:
                response = await acompletion(
                    model=model_name,
                    messages=messages,
                    api_key=settings.MODEL_HOSTS[model.hosts[0].slug].api_key,
                    **completion_params,
                    **kwargs,
                )
                process_tool_calls = await self._process_tool_calls(response=response, messages=messages)

            return TextGenerationDTO(
                text=response.choices[0].message.content,
                usage=TokenUsageDTO(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
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
            model_name = f"{model.hosts[0].slug}/{model.slug}"
            completion_params = self._get_completion_params(model_name)
            current_messages = self._prepare_messages(messages.copy(), model)
            
            while True:
                response = await acompletion(
                    model=model_name,
                    messages=current_messages,
                    stream=True,
                    api_key=settings.MODEL_HOSTS[model.hosts[0].slug].api_key,
                    stream_options={"include_usage": True},
                    **completion_params,
                    **kwargs,
                )

                # Buffer to accumulate the complete response
                complete_response_content = ""
                complete_response = None
                usage = None
                
                async for chunk in response:
                    if (
                        chunk.choices
                        and chunk.choices[0].delta
                        and chunk.choices[0].delta.content
                    ):
                        chunk_text = chunk.choices[0].delta.content
                        complete_response_content += chunk_text
                        yield StreamGenerationDTO(text=chunk_text, usage=None)
                    elif hasattr(chunk, "usage") and chunk.usage:
                        usage = TokenUsageDTO(
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens,
                        )
                        yield StreamGenerationDTO(text="", usage=usage)
                    
                    # Store the complete response object for tool call checking
                    if hasattr(chunk, "choices") and chunk.choices and complete_response is None:
                        complete_response = chunk
                
                # After streaming is complete, check for tool calls
                if complete_response and hasattr(complete_response.choices[0], "delta"):
                    # Reconstruct a message similar to non-streaming response
                    tool_message = {
                        "role": "assistant",
                        "content": complete_response_content,
                        "tool_calls": getattr(complete_response.choices[0].delta, "tool_calls", None)
                    }
                    
                    # Check if there are tool calls to process
                    if tool_message["tool_calls"]:
                        # Add the assistant's response to messages
                        current_messages.append(tool_message)
                        
                        # Process each tool call
                        for tool_call in tool_message["tool_calls"]:
                            function_name = tool_call.function.name
                            
                            try:
                                function_args = json.loads(tool_call.function.arguments)
                                result = self.tools_service.execute_function(function_name, function_args)
                                
                                # Add the function response to messages
                                current_messages.append({
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": result,
                                })
                            except Exception as e:
                                error_message = f"Error processing tool call: {str(e)}"
                                self.logger.error(error_message)
                                self.logger.error(traceback.format_exc())

                                current_messages.append({
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": json.dumps({"error": error_message}),
                                })
                        
                        # Continue the loop to make another call with updated messages
                        continue
                
                # If we get here, no tool calls were made or processed, so we're done
                break

        except litellm.BudgetExceededError as e:
            raise BudgetExceededError(e)
        except Exception as e:
            self.logger.error(f"Error in generate_response_stream: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise e

    async def count_tokens(
        self,
        messages: List[Dict[str, Any]],
        model: AiProviderModelDTO,
    ) -> int:
        return token_counter(model=f"{model.hosts[0].slug}/{model.slug}", messages=messages)

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

        return response
    
    async def _process_tool_calls(
        self,
        response: Any,
        messages: List[Dict[str, Any]],
    ) -> bool:
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if not tool_calls:
            return False

        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            
            try:
                function_args = json.loads(tool_call.function.arguments)
                result = self.tools_service.execute_function(function_name, function_args)

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result,
                })
            except Exception as e:
                error_message = f"Error processing tool call: {str(e)}"
                self.logger.error(error_message)
                self.logger.error(traceback.format_exc())
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"error": error_message}),
                })

        return True

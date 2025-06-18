import json
import traceback
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp
import litellm
from litellm import acompletion, token_counter
from litellm import utils as litellm_utils

from src.services.common.context import Context
from src.services.common.errors import (
    BadRequestError,
    BudgetExceededError,
    ModelApiError,
    NoAvailableHostError,
    NotFoundError,
)
from src.services.files.dto import FileDTO
from src.services.files.files_service import FilesService
from src.services.host_api_keys.host_api_key_service import HostApiKeyService
from src.services.inference.dto import (
    DefaultResponseGenerationOptionsDTO,
    StreamGenerationDTO,
    TextGenerationDTO,
    ThinkingContentDTO,
    ToolCallDTO,
    ToolCallFunctionDTO,
    ToolCallResultDTO,
)
from src.services.inference.tools_service import ToolsService
from src.services.usage_tracking.dto import TokenUsageDTO

from src.services.ai_providers.dto import AiModelsModalitiesDTO, AiProviderModelDTO, ModelHostDTO

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

    def __init__(self, context: Context, tools_service: ToolsService, host_api_key_service: HostApiKeyService,
                 files_service: FilesService):
        self.logger = get_logger(__name__)
        self.context = context
        self.tools_service = tools_service
        self.host_api_key_service = host_api_key_service
        self.files_service = files_service

    async def _get_api_key_for_host(self, host: ModelHostDTO) -> str:
        return await self.host_api_key_service.get_user_api_key_for_host(host.id)

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

                # quick hack for llama models
                if len(filtered_content) == 1 and message.get("role") == "assistant" and filtered_content[0].get(
                        "type") == "text":
                    filtered_content = filtered_content[0]['text']

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
        # TODO: extract generic try catch logic with catching exceptions
        try:
            selected_host = await self._select_available_host(model)

            api_key = await self._get_api_key_for_host(selected_host)
            model_slug = selected_host.model_slug

            model_name = f"{selected_host.slug}/{model_slug}"

            completion_params = self._get_completion_params(model_name, options)

            # Initialize accumulated usage tracking per model
            usage_by_model = {model.id: TokenUsageDTO(prompt_tokens=0, completion_tokens=0, total_tokens=0)}

            response = await acompletion(
                model=model_name,
                messages=self._prepare_messages(messages, model_slug),
                api_key=api_key,
                **completion_params,
                **kwargs,
            )

            # Accumulate usage from initial response
            if response.usage:
                usage_by_model[model.id].prompt_tokens += response.usage.prompt_tokens
                usage_by_model[model.id].completion_tokens += response.usage.completion_tokens
                usage_by_model[model.id].total_tokens += response.usage.total_tokens

            # Handle tool calls if present
            response_message = response.choices[0].message
            if response_message.tool_calls:
                await self._handle_tool_calls(
                    tool_calls=response_message.tool_calls,
                    messages=messages,
                    assistant_content=response_message.content or "",
                    usage_by_model=usage_by_model,
                )

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
                        usage_by_model[model.id].prompt_tokens += response.usage.prompt_tokens
                        usage_by_model[model.id].completion_tokens += response.usage.completion_tokens
                        usage_by_model[model.id].total_tokens += response.usage.total_tokens

                    response_message = response.choices[0].message
                    if response_message.tool_calls:
                        await self._handle_tool_calls(
                            tool_calls=response_message.tool_calls,
                            messages=messages,
                            assistant_content=response_message.content or "",
                            usage_by_model=usage_by_model,
                        )
                    else:
                        break

            return TextGenerationDTO(
                text=response.choices[0].message.content,
                usage=usage_by_model,
            )
        except litellm.BudgetExceededError as e:
            raise BudgetExceededError(e)
        except litellm.BadRequestError as e:
            raise BadRequestError(e)
        except litellm.APIError as e:
            raise ModelApiError(e)
        except litellm.NotFoundError as e:
            raise NotFoundError(resource_name="AiModel API", message=e)
        except Exception as e:
            self.logger.error(f"Error in generate_response: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise ModelApiError(e)

    async def generate_response_stream(
        self,
            models_modalities: AiModelsModalitiesDTO,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamGenerationDTO, None]:
        """Stream response from the model with error handling.

        This returns an AsyncGenerator that will either yield StreamGenerationResponse objects
        or, in case of an error, yield a single Exception object and then stop.
        """
        try:
            selected_host = await self._select_available_host(models_modalities.llm)

            api_key = await self._get_api_key_for_host(selected_host)
            model_slug = selected_host.model_slug

            model_name = f"{selected_host.slug}/{model_slug}"
            completion_params = self._get_completion_params(model_name)

            current_messages = self._prepare_messages(messages.copy(), model_slug)

            # Initialize accumulated usage tracking per model
            usage_by_model = {
                models_modalities.llm.id: TokenUsageDTO(prompt_tokens=0, completion_tokens=0, total_tokens=0)}

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
                accumulated_tool_calls = {}  # Dictionary to accumulate tool calls by index

                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta and hasattr(chunk.choices[0].delta,
                                                                            "reasoning_content") and chunk.choices[
                        0].delta.reasoning_content:
                        yield StreamGenerationDTO(text=None, usage=None,
                                                  reasoning=chunk.choices[0].delta.reasoning_content)

                    if chunk.choices and chunk.choices[0].delta and hasattr(chunk.choices[0].delta,
                                                                            "thinking_blocks") and chunk.choices[
                        0].delta.thinking_blocks:
                        yield StreamGenerationDTO(
                            text=None,
                            usage=None,
                            thinking=[
                                ThinkingContentDTO(type=block.get("type"), thinking=block.get("thinking"),
                                                   signature=block.get("signature"))
                                for block in chunk.choices[0].delta.thinking_blocks
                            ],
                        )

                    # Handle regular text content after reasoning
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        chunk_text = chunk.choices[0].delta.content
                        complete_response_content += chunk_text
                        yield StreamGenerationDTO(text=chunk_text)

                    elif hasattr(chunk, "usage") and chunk.usage:
                        # Accumulate usage from this iteration
                        usage_by_model[models_modalities.llm.id].prompt_tokens += chunk.usage.prompt_tokens
                        usage_by_model[models_modalities.llm.id].completion_tokens += chunk.usage.completion_tokens
                        usage_by_model[models_modalities.llm.id].total_tokens += chunk.usage.total_tokens

                    # Properly accumulate tool calls from streaming chunks
                    if chunk.choices and chunk.choices[0].delta and hasattr(chunk.choices[0].delta, "tool_calls") and \
                            chunk.choices[0].delta.tool_calls:

                        for tool_call_chunk in chunk.choices[0].delta.tool_calls:
                            if tool_call_chunk.index is not None:
                                index = tool_call_chunk.index

                                # Initialize tool call if not exists
                                if index not in accumulated_tool_calls:
                                    accumulated_tool_calls[index] = ToolCallDTO(
                                        id=tool_call_chunk.id or f"call_{index}_{hash(str(tool_call_chunk))}",
                                        type="function",
                                        function=ToolCallFunctionDTO(name="", arguments=""),
                                    )

                                # Update tool call with chunk data
                                if tool_call_chunk.id:
                                    accumulated_tool_calls[index].id = tool_call_chunk.id

                                if tool_call_chunk.function:
                                    if tool_call_chunk.function.name:
                                        accumulated_tool_calls[index].function.name = tool_call_chunk.function.name
                                    if tool_call_chunk.function.arguments:
                                        accumulated_tool_calls[
                                            index].function.arguments += tool_call_chunk.function.arguments

                # Convert accumulated tool calls to list
                final_tool_calls = list(accumulated_tool_calls.values()) if accumulated_tool_calls else None

                # Check if there are tool calls to process
                if final_tool_calls:
                    # Notify frontend that we are processing tool calls
                    yield StreamGenerationDTO(tools_calls=[tool_call.function.name for tool_call in final_tool_calls])

                    output = await self._handle_tool_calls(
                        models_modalities=models_modalities,
                        tool_calls=final_tool_calls,
                        messages=current_messages,
                        assistant_content=complete_response_content,
                        usage_by_model=usage_by_model,
                    )

                    if output:  # if we have output of the tool call, we need to yield it
                        yield StreamGenerationDTO(attachments=output)
                    # Continue the loop to make another call with updated messages
                    continue
                else:
                    yield StreamGenerationDTO(usage=usage_by_model)
                    break

        except litellm.BudgetExceededError as e:
            raise BudgetExceededError(e)
        except litellm.APIError as e:
            raise ModelApiError(e)
        except litellm.NotFoundError as e:
            raise NotFoundError(resource_name="AiModel API", message=e)
        except Exception as e:
            self.logger.error(f"Error in generate_response_stream: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise ModelApiError(e)

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

    # TODO: add parallel tools calling
    def _get_completion_params(self, model: str, options: Optional[DefaultResponseGenerationOptionsDTO] = None) -> Dict[
        str, Any]:
        response = {
            "drop_params": True,
        }

        if options and options.disable_tool_calls:
            return response

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

    async def _download_and_upload_image(self, image_url: str) -> Optional[FileDTO]:
        """Download image from URL and upload it to file service."""
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()
                image_data = await response.read()

                content_type = response.headers.get("Content-Type", "image/jpg")

                # Upload the actual image data
                return await self.files_service.upload_file(image_data, content_type=content_type)

    async def _process_tool_call_result(
            self,
            tool_call: Any,
            tool_call_result: ToolCallResultDTO,
            messages: List[Dict[str, Any]],
            usage_by_model: Dict[Any, TokenUsageDTO],
            models_modalities: Optional[AiModelsModalitiesDTO] = None,
    ) -> Optional[Any]:
        if tool_call_result.error:
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": json.dumps(tool_call_result.error),
                }
            )
            return None

        if tool_call.function.name == "image_generation":
            # Track image generation usage separately by model
            image_model_id = models_modalities.image_gen.id if models_modalities and models_modalities.image_gen else None
            if image_model_id:
                if image_model_id not in usage_by_model:
                    usage_by_model[image_model_id] = TokenUsageDTO(prompt_tokens=0, completion_tokens=0, total_tokens=0)

                usage_by_model[image_model_id].prompt_tokens += tool_call_result.usage.prompt_tokens
                usage_by_model[image_model_id].completion_tokens += tool_call_result.usage.completion_tokens
                usage_by_model[image_model_id].total_tokens += tool_call_result.usage.total_tokens

            file_dtos = []
            for result in tool_call_result.content:
                file_dto = await self._download_and_upload_image(result["url"])
                file_dtos.append(file_dto)

                # Create content with the uploaded file reference
                content = [
                    {"type": "text", "text": result["revised_prompt"]},
                    # {"type": "image_url", "image_url": {"url": result["url"]}},
                ]
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": json.dumps(content),
                    }
                )

            return file_dtos
        else:
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": json.dumps(tool_call_result.content),
                }
            )

    async def _handle_tool_calls(
        self,
            tool_calls: List[ToolCallDTO],
        messages: List[Dict[str, Any]],
            assistant_content: str,
            usage_by_model: Dict[Any, TokenUsageDTO],
            models_modalities: Optional[AiModelsModalitiesDTO] = None,
    ) -> Optional[Any]:  # TODO: need to refactor this
        if not tool_calls:
            return None

        # Add the assistant's response to messages
        messages.append({"role": "assistant", "content": assistant_content, "tool_calls": tool_calls})

        # Process each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name

            if isinstance(tool_call.function.arguments, str):
                function_args = json.loads(tool_call.function.arguments)
            else:
                function_args = tool_call.function.arguments

            # TODO: this is a bit of a hack, we should find a better way to do this
            if function_name == "image_generation":
                function_args["model"] = models_modalities.image_gen.name

            tool_result = await self.tools_service.execute_function(function_name, function_args)

            result = await self._process_tool_call_result(tool_call, tool_result, messages, usage_by_model,
                                                          models_modalities)
            if result:
                return result

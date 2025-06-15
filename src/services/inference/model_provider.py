import traceback
from typing import Any, AsyncGenerator, Dict, List, Optional

import litellm
from litellm import acompletion, token_counter
from litellm import utils as litellm_utils

from src.services.common.context import Context
from src.services.common.errors import BudgetExceededError
from src.services.inference.dto import DefaultResponseGenerationOptionsDTO, StreamGenerationDTO, TextGenerationDTO
from src.services.usage_tracking.dto import TokenUsageDTO

from src.services.ai_providers.dto import AiProviderDTO, AiProviderModelDTO

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

    def __init__(self, context: Context):
        self.logger = get_logger(__name__)
        self.context = context

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
            response = await acompletion(
                model=f"{model.host.slug}/{model.slug}",
                messages=self._prepare_messages(messages, model),
                api_key=settings.MODEL_HOSTS[model.host.slug].api_key,
                **kwargs,
            )
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
            response = await acompletion(
                model=f"{model.host.slug}/{model.slug}",
                messages=self._prepare_messages(messages, model),
                stream=True,
                api_key=settings.MODEL_HOSTS[model.host.slug].api_key,
                stream_options={"include_usage": True},
                **kwargs,
            )

            usage = None
            async for chunk in response:
                if (
                    chunk.choices
                    and chunk.choices[0].delta
                    and chunk.choices[0].delta.content
                ):
                    yield StreamGenerationDTO(
                        text=chunk.choices[0].delta.content, usage=None
                    )
                elif hasattr(chunk, "usage") and chunk.usage:
                    usage = TokenUsageDTO(
                        prompt_tokens=chunk.usage.prompt_tokens,
                        completion_tokens=chunk.usage.completion_tokens,
                        total_tokens=chunk.usage.total_tokens,
                    )
                    yield StreamGenerationDTO(text="", usage=usage)
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
        return token_counter(model=f"{model.host.slug}/{model.slug}", messages=messages)

    async def cost_per_token(self, model: AiProviderModelDTO, usage: TokenUsageDTO) -> float:
        prompt_tokens_cost_usd = model.price_input_token * usage.prompt_tokens
        completion_tokens_cost_usd = model.price_output_token * usage.completion_tokens
        return prompt_tokens_cost_usd + completion_tokens_cost_usd

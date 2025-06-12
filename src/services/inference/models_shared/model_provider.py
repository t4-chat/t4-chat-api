import traceback
from typing import Optional, Any, AsyncGenerator, List, Dict, Union, Tuple

from litellm import acompletion, token_counter
import litellm

from src.services.budget_service import BudgetService
from src.services.context import Context
from src.services.errors.errors import BudgetExceededError
from src.services.inference.config.text_options import DefaultResponseGenerationOptions
from src.services.inference.models.response_models import TextGenerationResponse, StreamGenerationResponse, Usage
from src.storage.models.ai_provider import AiProvider
from src.storage.models.ai_provider_model import AiProviderModel
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

    async def generate_response(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        **kwargs,
    ) -> Tuple[Optional[TextGenerationResponse], Optional[Exception]]:
        try:
            response = await acompletion(
                model=f"{provider.slug}/{model.slug}",
                messages=messages,
                api_key=settings.MODEL_PROVIDERS[provider.slug].api_key,
                **kwargs,
            )
            return TextGenerationResponse(
                text=response.choices[0].message.content,
                usage=Usage(
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
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        **kwargs,
    ) -> AsyncGenerator[Union[StreamGenerationResponse, Exception], None]:
        """Stream response from the model with error handling.

        This returns an AsyncGenerator that will either yield StreamGenerationResponse objects
        or, in case of an error, yield a single Exception object and then stop.
        """
        try:
            response = await acompletion(
                model=f"{provider.slug}/{model.slug}",
                messages=messages,
                stream=True,
                api_key=settings.MODEL_PROVIDERS[provider.slug].api_key,
                stream_options={"include_usage": True},
                **kwargs,
            )

            usage = None
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield StreamGenerationResponse(text=chunk.choices[0].delta.content, usage=None)
                elif hasattr(chunk, "usage") and chunk.usage:
                    usage = Usage(
                        prompt_tokens=chunk.usage.prompt_tokens,
                        completion_tokens=chunk.usage.completion_tokens,
                        total_tokens=chunk.usage.total_tokens,
                    )
                    yield StreamGenerationResponse(text="", usage=usage)
        except litellm.BudgetExceededError as e:
            raise BudgetExceededError(e)
        except Exception as e:
            self.logger.error(f"Error in generate_response_stream: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise e

    async def count_tokens(self, messages: List[Dict[str, Any]], provider: AiProvider, model: AiProviderModel) -> int:
        return token_counter(model=f"{provider.slug}/{model.slug}", messages=messages)

    async def cost_per_token(self, model: AiProviderModel, usage: Usage) -> float:
        prompt_tokens_cost_usd = model.price_input_token * usage.prompt_tokens
        completion_tokens_cost_usd = model.price_output_token * usage.completion_tokens
        return prompt_tokens_cost_usd + completion_tokens_cost_usd

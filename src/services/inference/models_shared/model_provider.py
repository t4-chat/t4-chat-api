from typing import Optional, Any, AsyncGenerator, List, Dict

from litellm import acompletion

from src.services.inference.config.text_options import DefaultResponseGenerationOptions
from src.services.inference.models.response_models import TextGenerationResponse, StreamGenerationResponse, Usage
from src.storage.models.ai_provider import AiProvider
from src.storage.models.ai_provider_model import AiProviderModel
from src.config import settings

# TODO:
# - add prompt caching when supported by the model provider
# - Citations API



class ModelProvider:
    """
    This is an absraction for a model provider.
    Here we can have different implementations for different model providers.
    For now we will just use litellm, but we can add more implementations in the future.
    """

    async def generate_response(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        **kwargs,
    ) -> TextGenerationResponse:
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

    async def generate_response_stream(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamGenerationResponse, None]:
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

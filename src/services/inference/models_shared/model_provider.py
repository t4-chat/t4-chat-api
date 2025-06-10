from typing import Optional, Any, AsyncGenerator, List, Dict

from litellm import acompletion

from src.services.inference.config.text_options import DefaultResponseGenerationOptions
from src.storage.models.ai_provider import AiProvider
from src.storage.models.ai_provider_model import AiProviderModel


class ModelProvider:
    """
    This is an absraction for a model provider.
    Here we can have different implementations for different model providers.
    For now we will just use litellm, but we can add more implementations in the future.
    """

    async def generate_response(
        self, provider: AiProvider, model: AiProviderModel, messages: List[Dict[str, Any]], options: Optional[DefaultResponseGenerationOptions] = None, **kwargs
    ) -> str:
        """Generate text based on the prompt (non-streaming)"""
        response = await acompletion(model=f"{provider.name.lower()}/{model.name}", messages=messages, mock_response="It's simple to use and easy to get started", **kwargs) # TODO: fix this lower, add slug to the provider 
        return response.choices[0].message.content

    async def generate_response_stream(
        self, provider: AiProvider, model: AiProviderModel, messages: List[Dict[str, Any]], options: Optional[DefaultResponseGenerationOptions] = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate text based on the prompt with streaming"""
        response = await acompletion(model=f"{provider.name.lower()}/{model.name}", messages=messages, stream=True, mock_response="It's simple to use and easy to get started", **kwargs) # TODO: fix this lower, add slug to the provider 
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

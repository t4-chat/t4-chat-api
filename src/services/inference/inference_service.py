from typing import Annotated, AsyncGenerator, Dict, Optional

from fastapi import Depends

from src.services.inference.config import TextGenerationOptions
from src.services.inference.models_shared import ModelProvider, TextGenerationProvider


class InferenceService:
    """Service for handling inference across different AI providers"""

    _instance: Optional["InferenceService"] = None

    def __init__(self):
        # Prevent direct instantiation
        if InferenceService._instance is not None:
            raise RuntimeError("InferenceService is a singleton. Use InferenceService.get_instance()")

        self._providers: Dict[ModelProvider, "TextGenerationProvider"] = {}

    @classmethod
    def get_instance(cls) -> "InferenceService":
        """Get the singleton instance of InferenceService"""
        if cls._instance is None:
            cls._instance = InferenceService()
        return cls._instance

    def register_provider(self, provider_type: ModelProvider, provider_instance: "TextGenerationProvider") -> None:
        """Register a provider instance with the service"""
        self._providers[provider_type] = provider_instance

    async def generate_text(self, provider: ModelProvider, model: str, prompt: str, options: Optional[TextGenerationOptions] = None, **kwargs) -> str:
        """Generate text using the specified provider and model (non-streaming)"""
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not registered")

        if options is None:
            options = TextGenerationOptions()

        return await self._providers[provider].generate_text(model=model, prompt=prompt, options=options, **kwargs)

    async def generate_text_stream(
        self, provider: ModelProvider, model: str, prompt: str, options: Optional[TextGenerationOptions] = None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate text using the specified provider and model with streaming"""
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not registered")

        if options is None:
            options = TextGenerationOptions()

        async for text_chunk in self._providers[provider].generate_text_stream(model=model, prompt=prompt, options=options, **kwargs):
            yield text_chunk


def get_inference_service() -> InferenceService:
    """Get the singleton instance of InferenceService"""
    return InferenceService.get_instance()


inference_service = Annotated[InferenceService, Depends(get_inference_service)]

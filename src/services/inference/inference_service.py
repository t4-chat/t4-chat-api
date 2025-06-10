from typing import Annotated, AsyncGenerator, Dict, List, Optional, Any

from fastapi import Depends
from requests import Session

from src.services.inference.config import DefaultResponseGenerationOptions
from src.services.inference.models_shared import ModelProvider
from src.storage.db import get_db
from src.storage.models.ai_provider import AiProvider
from src.storage.models.ai_provider_model import AiProviderModel


class InferenceService:
    """Service for handling inference across different AI providers"""

    def __init__(self, db: Session):
        self._db = db
        self._models_provider = ModelProvider()

    async def generate_response(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        **kwargs,
    ) -> str:
        """Generate response using the specified provider and model (non-streaming)"""
        return await self._models_provider.generate_response(provider=provider, model=model, messages=messages, options=options, **kwargs)

    async def generate_response_stream(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate response using the specified provider and model with streaming"""
        async for text_chunk in self._models_provider.generate_response_stream(provider=provider, model=model, messages=messages, options=options, **kwargs):
            yield text_chunk


def get_inference_service(db: Session = Depends(get_db)) -> InferenceService:
    """Get the inference service instance"""
    return InferenceService(db)


inference_service = Annotated[InferenceService, Depends(get_inference_service)]

from typing import AsyncGenerator, Dict, List, Optional, Any
from uuid import UUID

from requests import Session
from fastapi import BackgroundTasks

from src.services.inference.config import DefaultResponseGenerationOptions
from src.services.inference.models.response_models import TextGenerationResponse, StreamGenerationResponse
from src.services.inference.models_shared import ModelProvider
from src.services.background_task_service import BackgroundTaskService

from src.storage.models.ai_provider import AiProvider
from src.storage.models.ai_provider_model import AiProviderModel


class InferenceService:

    def __init__(
        self, 
        db: Session, 
        models_provider: ModelProvider, 
        background_task_service: BackgroundTaskService
    ):
        self._db = db
        self._models_provider = models_provider
        self._background_task_service = background_task_service

    async def generate_response(
        self,
        user_id: UUID,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        background_tasks: BackgroundTasks = None,
        **kwargs,
    ) -> TextGenerationResponse:
        resp = await self._models_provider.generate_response(
            provider=provider,
            model=model,
            messages=messages,
            options=options,
            **kwargs,
        )

        background_tasks.add_task(
            self._background_task_service.track_model_usage,
            user_id=user_id,
            model_id=model.id,
            usage=resp.usage
        )
        return resp

    async def generate_response_stream(
        self,
        user_id: UUID,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        background_tasks: BackgroundTasks = None,
        **kwargs,
    ) -> AsyncGenerator[StreamGenerationResponse, None]:
        usage = None
        async for chunk in self._models_provider.generate_response_stream(
            provider=provider,
            model=model,
            messages=messages,
            options=options,
            **kwargs,
        ):
            if chunk.usage:
                usage = chunk.usage
            yield chunk
            
        background_tasks.add_task(
            self._background_task_service.track_model_usage,
            user_id=user_id,
            model_id=model.id,
            usage=usage
        )

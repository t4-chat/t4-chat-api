from contextvars import Context
from typing import List

from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from src.api.schemas.ai_models import AiModelResponse
from src.services.ai_providers.ai_model_service import AiModelService
from src.containers.containers import AppContainer

router = APIRouter(prefix="/api/ai-models", tags=["ai-models"])


@router.get("", response_model=List[AiModelResponse])
@inject
async def get_ai_models(ai_model_service: AiModelService = Depends(Provide[AppContainer.ai_model_service])) -> List[AiModelResponse]:
    return await ai_model_service.get_ai_models()

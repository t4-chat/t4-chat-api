from typing import List

from fastapi import APIRouter

from src.api.schemas.ai_models import AiModelResponse
from src.containers.container import ai_model_service

router = APIRouter(prefix="/api/ai-models", tags=["ai-models"])


@router.get("", response_model=List[AiModelResponse])
async def get_ai_models(service: ai_model_service) -> List[AiModelResponse]:
    return await service.get_ai_models()

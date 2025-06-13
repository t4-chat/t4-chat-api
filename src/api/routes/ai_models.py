from typing import List

from fastapi import APIRouter

from src.api.schemas.ai_models import AiModelResponse
from src.containers.container import ai_model_service_dep

router = APIRouter(prefix="/api/ai-models", tags=["ai-models"])


@router.get("", response_model=List[AiModelResponse])
async def get_ai_models(ai_model_service: ai_model_service_dep) -> List[AiModelResponse]:
    return await ai_model_service.get_ai_models()

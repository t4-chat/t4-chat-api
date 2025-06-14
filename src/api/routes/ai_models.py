from typing import List

from fastapi import APIRouter

from src.api.schemas.ai_models import AiModelResponseSchema
from src.containers.container import AiModelServiceDep

router = APIRouter(prefix="/api/ai-models", tags=["ai-models"])


@router.get("", response_model=List[AiModelResponseSchema])
async def get_ai_models(
    ai_model_service: AiModelServiceDep,
) -> List[AiModelResponseSchema]:
    return await ai_model_service.get_ai_models()

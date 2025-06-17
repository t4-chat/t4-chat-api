from typing import List

from fastapi import APIRouter

from src.api.schemas.ai_models import AiModelResponseSchema
from src.containers.container import AiModelServiceDep, LimitsServiceDep
from src.services.ai_providers.dto import AiProviderModelDTO

router = APIRouter(prefix="/api/ai-models", tags=["AI Models"])


@router.get("", response_model=List[AiModelResponseSchema])
async def get_ai_models(
    ai_model_service: AiModelServiceDep,
    limits_service: LimitsServiceDep
) -> List[AiModelResponseSchema]:
    models = await ai_model_service.get_ai_models()

    result = [AiModelResponseSchema.model_validate(model) for model in models]
    model_ids = [model.id for model in models]
    limits = await limits_service.get_limits(model_ids=model_ids)
    limits_models_ids = set([limit.model_id for limit in limits])

    for model in result:
        model.only_with_byok = model.id not in limits_models_ids

    return result

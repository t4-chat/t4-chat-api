from typing import Dict, List, Optional

from fastapi import APIRouter, Query, Request

from src.services.common.filters import FiltersParser, SQLAlchemyFilterBuilder

from src.storage.models.ai_provider_model import AiProviderModel

from src.api.schemas.ai_models import AiModelResponseSchema
from src.containers.container import AiModelServiceDep, LimitsServiceDep

router = APIRouter(prefix="/api/ai-models", tags=["AI Models"])


@router.get("", response_model=List[AiModelResponseSchema])
async def get_ai_models(
        request: Request,
    ai_model_service: AiModelServiceDep,
        limits_service: LimitsServiceDep,
        modalities: Optional[List[str]] = Query(None, alias="filter[modalities]",
                                                description="Filter models by modalities (e.g., text, image, audio, vision, video)"),
) -> List[AiModelResponseSchema]:
    # Parse filter parameters from query string
    query_params = dict(request.query_params)
    filter_specs = FiltersParser.parse_filters(query_params)

    # Build SQLAlchemy filter conditions
    custom_filter = SQLAlchemyFilterBuilder.build_filters(AiProviderModel, filter_specs)

    # Get filtered models
    models = await ai_model_service.get_ai_models(custom_filter=custom_filter)

    result = [AiModelResponseSchema.model_validate(model) for model in models]

    if not ai_model_service.context.is_authenticated:
        return result
    
    model_ids = [model.id for model in models]
    limits = await limits_service.get_limits(model_ids=model_ids)
    limits_models_ids = set([limit.model_id for limit in limits])

    for model in result:
        model.only_with_byok = model.id not in limits_models_ids

    return result

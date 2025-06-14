from typing import List

from fastapi import APIRouter

from src.api.schemas.ai_providers import AiProviderResponseSchema
from src.containers.container import AiProviderServiceDep

router = APIRouter(prefix="/api/ai-providers", tags=["ai-providers"])

# DEPRECATED not working
@router.get("", response_model=List[AiProviderResponseSchema])
async def get_ai_providers(
    ai_provider_service: AiProviderServiceDep,
) -> List[AiProviderResponseSchema]:
    return await ai_provider_service.get_ai_providers()

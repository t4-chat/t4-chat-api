from typing import List

from fastapi import APIRouter

from src.api.schemas.ai_provider import AiProviderResponse
from src.containers.container import ai_provider_service

router = APIRouter(prefix="/api/ai-providers", tags=["ai-providers"])


@router.get("", response_model=List[AiProviderResponse])
async def get_ai_providers(
    provider_service: ai_provider_service
) -> List[AiProviderResponse]:
    return await provider_service.get_ai_providers()

from typing import List

from fastapi import APIRouter, Depends

from src.api.models.ai_provider import AiProviderResponse
from src.services.ai_provider_service import AiProviderService, ai_provider_service

router = APIRouter(prefix="/api/ai-providers", tags=["ai-providers"])


@router.get("", response_model=List[AiProviderResponse])
def get_ai_providers(ai_provider_service: ai_provider_service) -> List[AiProviderResponse]:
    return ai_provider_service.get_ai_providers()

from fastapi import APIRouter
from services.ai_provider_service import AiProviderService, ai_provider_service
from api.models.ai_provider import AiProviderResponse
from typing import List

router = APIRouter(
    prefix="/api/ai-providers",
    tags=["ai-providers"]
)

@router.get("", response_model=List[AiProviderResponse])
def get_ai_providers(ai_provider_service: ai_provider_service):
    return ai_provider_service.get_ai_providers()

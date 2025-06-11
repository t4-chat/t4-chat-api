from typing import List

from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from src.api.models.ai_provider import AiProviderResponse
from src.services.ai_providers.ai_provider_service import AiProviderService
from src.containers.containers import AppContainer

router = APIRouter(prefix="/api/ai-providers", tags=["ai-providers"])


@router.get("", response_model=List[AiProviderResponse])
@inject
def get_ai_providers(
    ai_provider_service: AiProviderService = Depends(Provide[AppContainer.ai_provider_service])
) -> List[AiProviderResponse]:
    return ai_provider_service.get_ai_providers()

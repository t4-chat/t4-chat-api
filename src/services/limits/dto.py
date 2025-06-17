from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from src.services.ai_providers.dto import AiProviderModelDTO


class UtilizationDTO(BaseModel):
    model: AiProviderModelDTO
    
    total_tokens: int
    max_tokens: int
    percentage: float


class LimitDTO(BaseModel):
    model_id: UUID
    max_tokens: int

    class Config:
        from_attributes = True

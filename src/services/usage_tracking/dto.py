from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from src.services.user.dto import UserDTO

from src.services.ai_providers.dto import AiProviderModelDTO


class TokenUsageDTO(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class UsageDTO(TokenUsageDTO):
    user_id: UUID
    model_id: UUID

    created_at: datetime

    class Config:
        from_attributes = True


class AggregatedUsageItemDTO(TokenUsageDTO):
    date: Optional[datetime] = None
    
    model_id: Optional[UUID] = None
    model_name: Optional[str] = None

    user_id: Optional[UUID] = None
    user_email: Optional[str] = None


class UsageAggregationDTO(BaseModel):
    data: List[AggregatedUsageItemDTO]
    total: TokenUsageDTO

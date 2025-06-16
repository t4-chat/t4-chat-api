from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class UtilizationDTO(BaseModel):
    model_id: UUID
    total_tokens: int
    percentage: float


class LimitDTO(BaseModel):
    model_id: UUID
    max_tokens: int

    class Config:
        from_attributes = True

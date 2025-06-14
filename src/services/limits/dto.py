from typing import List

from pydantic import BaseModel, Field


class UtilizationDTO(BaseModel):
    model_id: int
    total_tokens: int
    percentage: float


class LimitDTO(BaseModel):
    model_id: int
    max_tokens: int

    class Config:
        from_attributes = True

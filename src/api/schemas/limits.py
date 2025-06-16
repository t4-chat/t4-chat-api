from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class UtilizationResponseSchema(BaseModel):
    model_id: UUID = Field(..., description="The id of the model used")
    total_tokens: int = Field(..., description="The total number of tokens used")
    max_tokens: int = Field(..., description="The maximum number of tokens allowed")
    percentage: float = Field(..., description="The percentage of the limit used")

    class Config:
        from_attributes = True


class UtilizationsResponseSchema(BaseModel):
    utilizations: List[UtilizationResponseSchema] = Field(
        ..., description="The list of utilizations"
    )

    class Config:
        from_attributes = True


class LimitResponseSchema(BaseModel):
    model_id: UUID = Field(..., description="The id of the model used")
    max_tokens: int = Field(..., description="The maximum number of tokens allowed")

    class Config:
        from_attributes = True


class LimitsResponseSchema(BaseModel):
    limits: List[LimitResponseSchema] = Field(..., description="The list of limits")

    class Config:
        from_attributes = True

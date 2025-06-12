from typing import List
from pydantic import BaseModel, Field


class UtilizationResponse(BaseModel):
    model_id: int = Field(..., description="The id of the model used")
    total_tokens: int = Field(..., description="The total number of tokens used")
    percentage: float = Field(..., description="The percentage of the limit used")

    class Config:
        from_attributes = True


class UtilizationsResponse(BaseModel):
    utilizations: List[UtilizationResponse] = Field(..., description="The list of utilizations")

    class Config:
        from_attributes = True


class LimitResponse(BaseModel):
    model_id: int = Field(..., description="The id of the model used")
    max_tokens: int = Field(..., description="The maximum number of tokens allowed")

    class Config:
        from_attributes = True


class LimitsResponse(BaseModel):
    limits: List[LimitResponse] = Field(..., description="The list of limits")

    class Config:
        from_attributes = True

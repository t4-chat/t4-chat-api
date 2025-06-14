from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class AggregationType(str, Enum):
    minute = "minute"
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    model = "model"
    user = "user"


class BudgetResponseSchema(BaseModel):
    budget: float
    usage: float

    class Config:
        from_attributes = True


class BaseAggregatedUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int



class UnifiedAggregatedUsage(BaseAggregatedUsage):
    date: Optional[datetime] = None
    
    model_id: Optional[int] = None
    model_name: Optional[str] = None
    
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None


class UsageAggregationResponseSchema(BaseModel):
    data: List[UnifiedAggregatedUsage]
    total: BaseAggregatedUsage = Field(..., description="Total usage across all aggregated data")

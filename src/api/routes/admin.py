from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query

from src.api.schemas.admin import AggregationType, BudgetResponseSchema, UsageAggregationResponseSchema
from src.containers.container import BudgetServiceDep, UsageTrackingServiceDep

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/budget", response_model=BudgetResponseSchema)
async def get_budget(
    budget_service: BudgetServiceDep,
):
    return await budget_service.get_budget()


@router.get("/usage", response_model=UsageAggregationResponseSchema)
async def get_usage(
    usage_tracking_service: UsageTrackingServiceDep,
    aggregation: AggregationType = Query(AggregationType.day, description="How to aggregate the usage data"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    model_id: Optional[int] = Query(None, description="Filter by model ID"),
):
    return await usage_tracking_service.get_aggregated_usage(
        aggregation=aggregation,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        model_id=model_id,
    )

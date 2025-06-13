from fastapi import APIRouter

from src.api.schemas.limits import UtilizationsResponse, LimitsResponse
from src.containers.container import limits_service


router = APIRouter(
    prefix="/api/utilization",
    tags=["Utilization"],
)


@router.get("")
async def get_utilizations(
    service: limits_service,
):
    return UtilizationsResponse(utilizations=await service.get_utilizations())


@router.get("/limits")
async def get_limits(
    service: limits_service,
):
    return LimitsResponse(limits=await service.get_limits())

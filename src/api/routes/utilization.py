from fastapi import APIRouter

from src.api.schemas.limits import UtilizationsResponse, LimitsResponse
from src.containers.container import limits_service_dep


router = APIRouter(
    prefix="/api/utilization",
    tags=["Utilization"],
)


@router.get("")
async def get_utilizations(
    limits_service: limits_service_dep,
):
    return UtilizationsResponse(utilizations=await limits_service.get_utilizations())


@router.get("/limits")
async def get_limits(
    limits_service: limits_service_dep,
):
    return LimitsResponse(limits=await limits_service.get_limits())

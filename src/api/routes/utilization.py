from fastapi import APIRouter

from src.api.schemas.limits import LimitsResponseSchema, UtilizationsResponseSchema
from src.containers.container import LimitsServiceDep

router = APIRouter(
    prefix="/api/utilization",
    tags=["Utilization"],
)


@router.get("")
async def get_utilizations(
    limits_service: LimitsServiceDep,
):
    return UtilizationsResponseSchema(
        utilizations=await limits_service.get_utilizations()
    )


@router.get("/limits")
async def get_limits(
    limits_service: LimitsServiceDep,
) -> LimitsResponseSchema:
    return LimitsResponseSchema(limits=await limits_service.get_limits())

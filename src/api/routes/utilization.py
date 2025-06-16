from fastapi import APIRouter

from src.api.schemas.limits import LimitsResponseSchema, UtilizationsResponseSchema
from src.containers.container import LimitsServiceDep

router = APIRouter(
    prefix="/api/utilization",
    tags=["Utilization"],
)


@router.get("", response_model=UtilizationsResponseSchema)
async def get_utilizations(
    limits_service: LimitsServiceDep,
):
    return UtilizationsResponseSchema(
        utilizations=await limits_service.get_utilizations()
    )


@router.get("/limits", response_model=LimitsResponseSchema)
async def get_limits(
    limits_service: LimitsServiceDep,
) -> LimitsResponseSchema:
    return LimitsResponseSchema(limits=await limits_service.get_limits())

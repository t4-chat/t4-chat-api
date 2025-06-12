from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from src.api.schemas.limits import UtilizationsResponse, LimitsResponse
from src.services.limits_service import LimitsService
from src.containers.containers import AppContainer


router = APIRouter(
    prefix="/api/utilization",
    tags=["Utilization"],
)


@router.get("")
@inject
async def get_utilizations(
    limits_service: LimitsService = Depends(Provide[AppContainer.limits_service]),
):
    return UtilizationsResponse(utilizations=await limits_service.get_utilizations())


@router.get("/limits")
@inject
async def get_limits(
    limits_service: LimitsService = Depends(Provide[AppContainer.limits_service]),
):
    return LimitsResponse(limits=await limits_service.get_limits())

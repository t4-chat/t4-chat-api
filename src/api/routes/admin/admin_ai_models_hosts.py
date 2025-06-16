from fastapi import APIRouter
from typing import List
from uuid import UUID

from src.api.schemas.ai_models import AiModelHostResponseSchema, EditAiModelHostRequestSchema
from src.containers.container import AiModelHostServiceDep
from src.services.ai_providers.dto import EditAiModelHostDTO

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/model-hosts", response_model=List[AiModelHostResponseSchema])
async def get_hosts(
    ai_model_host_service: AiModelHostServiceDep,
):
    return await ai_model_host_service.get_hosts()


@router.get("/model-hosts/{host_id}", response_model=AiModelHostResponseSchema)
async def get_host(
    ai_model_host_service: AiModelHostServiceDep,
    host_id: UUID,
):
    return await ai_model_host_service.get_by_id(id=host_id)


@router.post("/model-hosts", response_model=AiModelHostResponseSchema)
async def add_host(
    ai_model_host_service: AiModelHostServiceDep,
    add_host_request: EditAiModelHostRequestSchema,
):
    ai_model_host_dto = EditAiModelHostDTO.model_validate(add_host_request)
    return await ai_model_host_service.add(ai_model_host_dto)


@router.put("/model-hosts/{host_id}", response_model=AiModelHostResponseSchema)
async def update_host(
    ai_model_host_service: AiModelHostServiceDep,
    host_id: UUID,
    update_host_request: EditAiModelHostRequestSchema,
):
    ai_model_host_dto = EditAiModelHostDTO.model_validate(update_host_request)
    return await ai_model_host_service.update(id=host_id, host_dto=ai_model_host_dto)


@router.delete("/model-hosts/{host_id}")
async def delete_host(
    ai_model_host_service: AiModelHostServiceDep,
    host_id: UUID,
):
    await ai_model_host_service.delete(host_id)
    return {"status": "success"}
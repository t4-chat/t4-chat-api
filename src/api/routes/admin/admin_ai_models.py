from fastapi import APIRouter
from typing import List
from uuid import UUID

from src.api.schemas.ai_models import AiModelResponseForAdminSchema, EditAiModelRequestSchema
from src.containers.container import AiModelServiceDep
from src.services.ai_providers.dto import EditAiModelDTO

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/ai-models", response_model=List[AiModelResponseForAdminSchema])
async def get_ai_models(
    ai_model_service: AiModelServiceDep,
):
    return await ai_model_service.get_ai_models(only_active=False)


@router.get("/ai-models/{ai_model_id}", response_model=AiModelResponseForAdminSchema)
async def get_ai_model(
    ai_model_service: AiModelServiceDep,
    ai_model_id: UUID,
):
    return await ai_model_service.get_by_id(id=ai_model_id)


@router.post("/ai-models", response_model=AiModelResponseForAdminSchema)
async def add_ai_model(
    ai_model_service: AiModelServiceDep,
    add_ai_model_request: EditAiModelRequestSchema,
):
    ai_model_dto = EditAiModelDTO.model_validate(add_ai_model_request)
    return await ai_model_service.add(ai_model_dto)


@router.put("/ai-models/{ai_model_id}", response_model=AiModelResponseForAdminSchema)
async def update_ai_model(
    ai_model_service: AiModelServiceDep,
    ai_model_id: UUID,
    update_ai_model_request: EditAiModelRequestSchema,
):
    ai_model_dto = EditAiModelDTO.model_validate(update_ai_model_request)
    return await ai_model_service.update(id=ai_model_id, ai_model_dto=ai_model_dto)

@router.delete("/ai-models/{ai_model_id}")
async def delete_ai_model(
    ai_model_service: AiModelServiceDep,
    ai_model_id: UUID,
):
    await ai_model_service.delete(id=ai_model_id)
    return {"status": "success"}
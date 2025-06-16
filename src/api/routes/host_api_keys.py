from typing import List
from uuid import UUID

from fastapi import APIRouter

from src.services.host_api_keys.dto import CreateHostApiKeyDTO, UpdateHostApiKeyDTO

from src.api.schemas.host_api_keys import HostApiKeyCreateSchema, HostApiKeyResponseSchema, HostApiKeyUpdateSchema
from src.containers.container import HostApiKeyServiceDep

router = APIRouter(prefix="/api/host-api-keys", tags=["Host API Keys"])


@router.post("", response_model=HostApiKeyResponseSchema)
async def create_host_api_key(
    data: HostApiKeyCreateSchema,
    service: HostApiKeyServiceDep
) -> HostApiKeyResponseSchema:
    create_dto = CreateHostApiKeyDTO(
        host_id=data.host_id,
        name=data.name,
        api_key=data.api_key
    )
    result = await service.create_api_key(create_dto)
    return HostApiKeyResponseSchema(
        id=result.id,
        host_id=result.host_id,
        name=result.name,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at
    )


@router.get("", response_model=List[HostApiKeyResponseSchema])
async def get_host_api_keys(
    service: HostApiKeyServiceDep,
    host_id: UUID | None = None
) -> List[HostApiKeyResponseSchema]:
    results = await service.get_api_keys(host_id)
    return [
        HostApiKeyResponseSchema(
            id=result.id,
            host_id=result.host_id,
            name=result.name,
            is_active=result.is_active,
            created_at=result.created_at,
            updated_at=result.updated_at
        )
        for result in results
    ]


@router.get("/{key_id}", response_model=HostApiKeyResponseSchema)
async def get_host_api_key(
    key_id: UUID,
    service: HostApiKeyServiceDep
) -> HostApiKeyResponseSchema:
    result = await service.get_api_key(key_id)
    return HostApiKeyResponseSchema(
        id=result.id,
        host_id=result.host_id,
        name=result.name,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at
    )


@router.put("/{key_id}", response_model=HostApiKeyResponseSchema)
async def update_host_api_key(
    key_id: UUID,
    data: HostApiKeyUpdateSchema,
    service: HostApiKeyServiceDep
) -> HostApiKeyResponseSchema:
    update_dto = UpdateHostApiKeyDTO(
        name=data.name,
        api_key=data.api_key,
        is_active=data.is_active
    )
    result = await service.update_api_key(key_id, update_dto)
    return HostApiKeyResponseSchema(
        id=result.id,
        host_id=result.host_id,
        name=result.name,
        is_active=result.is_active,
        created_at=result.created_at,
        updated_at=result.updated_at
    )


@router.delete("/{key_id}")
async def delete_host_api_key(
    key_id: UUID,
    service: HostApiKeyServiceDep
) -> dict:
    await service.delete_api_key(key_id)
    return {"message": "API key deleted successfully"} 
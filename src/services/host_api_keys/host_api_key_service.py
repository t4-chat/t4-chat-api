from typing import List, Optional
from uuid import UUID

from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto
from src.services.common.errors import BadRequestError, NotFoundError
from src.services.host_api_keys.dto import CreateHostApiKeyDTO, HostApiKeyDTO, UpdateHostApiKeyDTO
from src.services.host_api_keys.encryption import ApiKeyEncryption

from src.storage.base_repo import BaseRepository
from src.storage.models.host_api_key import HostApiKey


class HostApiKeyService:
    def __init__(self, context: Context, host_api_key_repo: BaseRepository[HostApiKey]):
        self.context = context
        self.host_api_key_repo = host_api_key_repo
        self._encryption = ApiKeyEncryption()

    @convert_to_dto
    async def create_api_key(self, data: CreateHostApiKeyDTO) -> HostApiKeyDTO:
        # Remove existing key if it exists
        await self.host_api_key_repo.delete_by_filter(
            filter=(HostApiKey.user_id == self.context.user_id) & (HostApiKey.host_id == data.host_id)
        )
        
        # Create new key
        encrypted_key = self._encryption.encrypt(data.api_key)
        api_key = HostApiKey(
            user_id=self.context.user_id,
            host_id=data.host_id,
            name=data.name,
            encrypted_key=encrypted_key,
            is_active=True
        )
        
        return await self.host_api_key_repo.add(api_key)

    @convert_to_dto
    async def get_api_keys(self, host_id: UUID | None = None) -> List[HostApiKeyDTO]:
        base_filter = HostApiKey.user_id == self.context.user_id
        if host_id:
            filter_condition = base_filter & (HostApiKey.host_id == host_id)
            return await self.host_api_key_repo.select(filter=filter_condition)
        return await self.host_api_key_repo.select(filter=base_filter)

    @convert_to_dto
    async def get_api_key(self, key_id: UUID) -> Optional[HostApiKeyDTO]:
        api_key = await self.host_api_key_repo.get(
            filter=(HostApiKey.id == key_id) & (HostApiKey.user_id == self.context.user_id)
        )
        if not api_key:
            raise NotFoundError("API key not found")
        return api_key

    @convert_to_dto
    async def update_api_key(self, key_id: UUID, data: UpdateHostApiKeyDTO) -> HostApiKeyDTO:
        api_key = await self.host_api_key_repo.get(
            filter=(HostApiKey.id == key_id) & (HostApiKey.user_id == self.context.user_id)
        )
        if not api_key:
            raise NotFoundError("API key not found")

        if data.name is not None:
            api_key.name = data.name
        if data.api_key is not None:
            api_key.encrypted_key = self._encryption.encrypt(data.api_key)
        if data.is_active is not None:
            api_key.is_active = data.is_active

        return await self.host_api_key_repo.update(api_key)

    async def delete_api_key(self, key_id: UUID) -> None:
        api_key = await self.host_api_key_repo.get(
            filter=(HostApiKey.id == key_id) & (HostApiKey.user_id == self.context.user_id)
        )
        if not api_key:
            raise NotFoundError("API key not found")
        
        await self.host_api_key_repo.delete_by_filter(
            filter=(HostApiKey.id == key_id) & (HostApiKey.user_id == self.context.user_id)
        )

    async def get_user_host_ids_with_active_keys(self) -> set[UUID]:
        api_keys = await self.host_api_key_repo.select(
            filter=(HostApiKey.user_id == self.context.user_id) & (HostApiKey.is_active == True)
        )
        return {key.host_id for key in api_keys}

    async def get_user_api_key_for_host(self, host_id: UUID) -> Optional[str]:
        api_key = await self.host_api_key_repo.get(
            filter=(HostApiKey.user_id == self.context.user_id) & 
                   (HostApiKey.host_id == host_id) & 
                   (HostApiKey.is_active == True)
        )
        if api_key:
            return self._encryption.decrypt(api_key.encrypted_key)
        return None
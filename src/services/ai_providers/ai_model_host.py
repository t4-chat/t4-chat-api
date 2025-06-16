from typing import List
from uuid import UUID

from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto
from src.services.common.errors import BadRequestError

from src.services.ai_providers.dto import EditAiModelHostDTO, ModelHostDTO

from src.storage.base_repo import BaseRepository
from src.storage.models.model_host import ModelHost
from src.storage.models.model_host_association import ModelHostAssociation


class AiModelHostService:
    def __init__(self, context: Context, ai_model_host_repo: BaseRepository[ModelHost]):
        self.context = context
        self.ai_model_host_repo = ai_model_host_repo

    @convert_to_dto
    async def get_hosts(self) -> List[ModelHostDTO]:
        return await self.ai_model_host_repo.select(includes=[ModelHost.model_associations])
    
    @convert_to_dto
    async def get_by_id(self, id: UUID) -> ModelHostDTO:
        return await self.ai_model_host_repo.get(filter=ModelHost.id == id, includes=[ModelHost.model_associations])
    
    @convert_to_dto
    async def add(self, host_dto: EditAiModelHostDTO) -> ModelHostDTO:
        existing_host = await self.ai_model_host_repo.get(filter=ModelHost.slug == host_dto.slug)

        if existing_host:
            raise BadRequestError(f"Host with slug {host_dto.slug} already exists")
            
        host = ModelHost(
            name=host_dto.name,
            slug=host_dto.slug,
            is_active=host_dto.is_active,
            model_associations=[ModelHostAssociation(model_id=assoc.model_id, model_slug=assoc.model_slug, priority=assoc.priority) for assoc in host_dto.model_associations],
        )

        return await self.ai_model_host_repo.add(host)
    
    @convert_to_dto
    async def update(self, id: UUID, host_dto: EditAiModelHostDTO) -> ModelHostDTO:
        existing_host = await self.ai_model_host_repo.get(filter=ModelHost.id == id, includes=[ModelHost.model_associations])

        if not existing_host:
            raise BadRequestError(f"Host with id {id} not found")
        
        existing_host.name = host_dto.name
        existing_host.slug = host_dto.slug
        existing_host.is_active = host_dto.is_active
        existing_host.model_associations.clear()
        existing_host.model_associations = [ModelHostAssociation(model_id=assoc.model_id, model_slug=assoc.model_slug, priority=assoc.priority) for assoc in host_dto.model_associations]

        return await self.ai_model_host_repo.update(existing_host)
    
    async def delete(self, id: UUID) -> None:
        return await self.ai_model_host_repo.delete_by_filter(filter=ModelHost.id == id)

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_

from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto

from src.services.ai_providers.dto import AiProviderModelDTO, EditAiModelDTO

from src.services.common.errors import BadRequestError
from src.storage.base_repo import BaseRepository
from src.storage.models import AiProviderModel
from src.storage.models.ai_provider import AiProvider
from src.storage.models.model_host_association import ModelHostAssociation
from src.storage.models.limits import Limits
from src.storage.models.usage import Usage


class AiModelService:
    def __init__(
        self, context: Context,
        ai_model_repo: BaseRepository[AiProviderModel],
        limits_repo: BaseRepository[Limits],
        usage_repo: BaseRepository[Usage]
    ):
        self.context = context
        self.ai_model_repo = ai_model_repo
        self.limits_repo = limits_repo
        self.usage_repo = usage_repo

    @convert_to_dto
    async def get_ai_models(self, only_active: bool = True) -> List[AiProviderModelDTO]:
        filter = AiProviderModel.is_active == True if only_active else None
        return await self.ai_model_repo.select(filter=filter, includes=[AiProviderModel.provider, AiProviderModel.host_associations, AiProviderModel.hosts])
    
    @convert_to_dto
    async def get_by_id(self, id: UUID) -> Optional[AiProviderModelDTO]:
        return await self.ai_model_repo.get(filter=AiProviderModel.id == id, includes=[AiProviderModel.provider, AiProviderModel.host_associations, AiProviderModel.hosts])

    @convert_to_dto
    async def get_model(self, model_id: UUID) -> Optional[AiProviderModelDTO]:
        return await self.ai_model_repo.get(
            filter=AiProviderModel.id == model_id, includes=[AiProviderModel.provider, AiProviderModel.host_associations, AiProviderModel.hosts]
        )

    @convert_to_dto
    async def get_model_by_path(self, path: str) -> Optional[AiProviderModelDTO]:
        provider_slug, model_name = path.split("/")
        model = await self.ai_model_repo.get(
            joins=[AiProviderModel.provider],
            filter=and_(
                AiProvider.slug == provider_slug, AiProviderModel.name == model_name
            ),
            includes=[AiProviderModel.provider, AiProviderModel.host_associations, AiProviderModel.hosts],
        )
        return model
    
    @convert_to_dto
    async def add(self, ai_model_dto: EditAiModelDTO) -> AiProviderModelDTO:
        existing_model = await self.ai_model_repo.get(filter=AiProviderModel.slug == ai_model_dto.slug)

        if existing_model:
            raise BadRequestError(f"Model with slug {ai_model_dto.slug} already exists")
        
        ai_model = AiProviderModel(
            name=ai_model_dto.name,
            slug=ai_model_dto.slug,
            provider_id=ai_model_dto.provider_id,
            prompt_path=ai_model_dto.prompt_path,
            price_input_token=ai_model_dto.price_input_token,
            price_output_token=ai_model_dto.price_output_token,
            context_length=ai_model_dto.context_length,
            is_active=ai_model_dto.is_active,
            tags=ai_model_dto.tags,
            host_associations=[ModelHostAssociation(host_id=assoc.host_id, priority=assoc.priority) for assoc in ai_model_dto.host_associations],
        )

        return await self.ai_model_repo.add(ai_model)
    
    @convert_to_dto
    async def update(self, id: UUID, ai_model_dto: EditAiModelDTO) -> AiProviderModelDTO:
        existing_model = await self.ai_model_repo.get(filter=AiProviderModel.id == id, includes=[AiProviderModel.provider, AiProviderModel.host_associations, AiProviderModel.hosts])

        if not existing_model:
            raise BadRequestError(f"Model with id {ai_model_dto.id} not found")
        
        existing_model.name = ai_model_dto.name
        existing_model.slug = ai_model_dto.slug
        existing_model.provider_id = ai_model_dto.provider_id
        existing_model.prompt_path = ai_model_dto.prompt_path
        existing_model.price_input_token = ai_model_dto.price_input_token
        existing_model.price_output_token = ai_model_dto.price_output_token
        existing_model.context_length = ai_model_dto.context_length
        existing_model.is_active = ai_model_dto.is_active
        existing_model.tags = ai_model_dto.tags
        existing_model.host_associations.clear()
        existing_model.host_associations = [ModelHostAssociation(host_id=assoc.host_id, priority=assoc.priority) for assoc in ai_model_dto.host_associations]

        return await self.ai_model_repo.update(existing_model)
    
    async def delete(self, id: UUID) -> None:
        dependent_records = []
        
        limits_count = await self.limits_repo.count(filter=Limits.model_id == id)
        if limits_count > 0:
            dependent_records.append(f"{limits_count} limit record(s)")

        usage_count = await self.usage_repo.count(filter=Usage.model_id == id)
        if usage_count > 0:
            dependent_records.append(f"{usage_count} usage record(s)")
        
        if len(dependent_records) > 0:
            raise BadRequestError(
                f"Cannot delete AI model. It is still referenced by: {', '.join(dependent_records)}. "
                f"Please remove or reassign these records before deleting the model."
            )
        
        return await self.ai_model_repo.delete_by_filter(filter=AiProviderModel.id == id)

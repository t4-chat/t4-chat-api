from typing import List, Optional

from sqlalchemy import and_

from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto

from src.services.ai_providers.dto import AiProviderModelDTO

from src.storage.base_repo import BaseRepository
from src.storage.models import AiProviderModel
from src.storage.models.ai_provider import AiProvider


class AiModelService:
    def __init__(
        self, context: Context, ai_model_repo: BaseRepository[AiProviderModel]
    ):
        self.context = context
        self.ai_model_repo = ai_model_repo

    @convert_to_dto
    async def get_ai_models(self) -> List[AiProviderModelDTO]:
        return await self.ai_model_repo.get_all(includes=[AiProviderModel.provider])

    @convert_to_dto
    async def get_model(self, model_id: int) -> Optional[AiProviderModelDTO]:
        return await self.ai_model_repo.get(
            filter=AiProviderModel.id == model_id, includes=[AiProviderModel.provider]
        )

    @convert_to_dto
    async def get_model_by_path(self, path: str) -> Optional[AiProviderModelDTO]:
        provider_slug, model_name = path.split("/")
        model = await self.ai_model_repo.get(
            joins=[AiProviderModel.provider],
            filter=and_(
                AiProvider.slug == provider_slug, AiProviderModel.name == model_name
            ),
            includes=[AiProviderModel.provider],
        )
        return model

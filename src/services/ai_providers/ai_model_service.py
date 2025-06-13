from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.context import Context
from src.storage.models import AiProviderModel
from src.storage.models.ai_provider import AiProvider


class AiModelService:
    def __init__(self, context: Context, db: AsyncSession):
        self.context = context
        self.db = db

    async def get_ai_models(self) -> List[AiProviderModel]:
        result = await self.db.execute(
            select(AiProviderModel).options(selectinload(AiProviderModel.provider))
        )
        return result.scalars().all()
    
    async def get_model(self, model_id: int) -> Optional[AiProviderModel]:
        results = await self.db.execute(select(AiProviderModel).options(selectinload(AiProviderModel.provider)).filter(AiProviderModel.id == model_id))
        return results.scalar_one_or_none()

    async def get_model_by_path(self, path: str) -> Optional[AiProviderModel]:
        provider_slug, model_name = path.split("/")
        results = await self.db.execute(
            select(AiProviderModel)
            .join(AiProviderModel.provider)
            .options(selectinload(AiProviderModel.provider))
            .filter(AiProvider.slug == provider_slug, AiProviderModel.name == model_name)
        )
        return results.scalar_one_or_none()

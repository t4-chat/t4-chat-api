from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.context import Context
from src.storage.models import AiProviderModel


class AiModelService:
    def __init__(self, context: Context, db: AsyncSession):
        self.context = context
        self.db = db

    async def get_ai_models(self) -> List[AiProviderModel]:
        result = await self.db.execute(
            select(AiProviderModel).options(selectinload(AiProviderModel.provider))
        )
        return result.scalars().all()

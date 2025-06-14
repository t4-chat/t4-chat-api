from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.context import Context
from src.storage.models import AiProvider


class AiProviderService:
    def __init__(self, context: Context, db: AsyncSession):
        self.context = context
        self.db = db

    async def get_ai_providers(self) -> List[AiProvider]:
        result = await self.db.execute(select(AiProvider).options(selectinload(AiProvider.models)))
        return result.scalars().all()

    async def get_provider(self, provider_id: int) -> Optional[AiProvider]:
        results = await self.db.execute(select(AiProvider).filter(AiProvider.id == provider_id))
        return results.scalar_one_or_none()
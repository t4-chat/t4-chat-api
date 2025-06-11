from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.context import Context
from src.storage.models import AiProvider


class AiProviderService:
    def __init__(self, context: Context, db: AsyncSession):
        self.context = context
        self.db = db

    async def get_ai_providers(self) -> List[AiProvider]:
        result = await self.db.execute(select(AiProvider))
        return result.scalars().all()

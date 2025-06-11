from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.api.schemas.ai_models import AiModelResponse

from src.storage.models import AiProviderModel


class AiModelService:
    def __init__(self, db: Session):
        self.db = db

    async def get_ai_models(self) -> List[AiProviderModel]:
        result = await self.db.execute(
            select(AiProviderModel).options(selectinload(AiProviderModel.provider))
        )
        return result.scalars().all()

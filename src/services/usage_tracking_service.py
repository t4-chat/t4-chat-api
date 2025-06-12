from typing import List
from uuid import UUID
from litellm import Usage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.services.context import Context
from src.storage.models.usage import Usage as UsageModel
from src.storage.models.user import User


class UsageTrackingService:
    def __init__(self, context: Context, db: AsyncSession):
        self.context = context
        self.db = db

    async def track_usage(self, user_id: UUID, model_id: int, usage: Usage):
        results = await self.db.execute(select(UsageModel).where(UsageModel.user_id == user_id, UsageModel.model_id == model_id))
        existing_usage = results.scalar_one_or_none()

        if existing_usage:
            # Update existing record by adding new token counts
            existing_usage.prompt_tokens += usage.prompt_tokens
            existing_usage.completion_tokens += usage.completion_tokens
            existing_usage.total_tokens += usage.total_tokens
        else:
            # Create a new record if none exists
            self.db.add(
                UsageModel(
                    user_id=user_id,
                    model_id=model_id,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                )
            )

        await self.db.commit()

    async def get_usage(self, model_id: int) -> UsageModel:
        results = await self.db.execute(select(UsageModel).where(UsageModel.user_id == self.context.user_id, UsageModel.model_id == model_id))
        return results.scalar_one_or_none()

    async def get_usages(self) -> List[UsageModel]:
        results = await self.db.execute(select(UsageModel).where(UsageModel.user_id == self.context.user_id))
        return results.scalars().all()

    async def get_group_usages(self, model_id: int) -> List[UsageModel]:
        results = await self.db.execute(
            select(UsageModel)
            .join(User, User.id == UsageModel.user_id)
            .where(UsageModel.model_id == model_id, User.group_name == select(User.group_name).where(User.id == self.context.user_id).scalar_subquery())
        )
        return results.scalars().all()

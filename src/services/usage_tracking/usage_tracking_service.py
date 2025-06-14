from typing import List
from uuid import UUID

from litellm import Usage as ModelUsage
from sqlalchemy import and_, select

from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto
from src.services.usage_tracking.dto import UsageDTO

from src.storage.base_repo import BaseRepository
from src.storage.models.usage import Usage
from src.storage.models.user import User


class UsageTrackingService:
    def __init__(self, context: Context, usage_model_repo: BaseRepository[Usage]):
        self.context = context
        self.usage_model_repo = usage_model_repo

    async def track_usage(self, user_id: UUID, model_id: int, usage: UsageDTO):
        existing_usage = await self.usage_model_repo.get(
            filter=and_(Usage.user_id == user_id, Usage.model_id == model_id)
        )

        if existing_usage:
            # Update existing record by adding new token counts
            existing_usage.prompt_tokens += usage.prompt_tokens
            existing_usage.completion_tokens += usage.completion_tokens
            existing_usage.total_tokens += usage.total_tokens
            await self.usage_model_repo.update(existing_usage)
        else:
            # Create a new record if none exists
            await self.usage_model_repo.add(
                Usage(
                    user_id=user_id,
                    model_id=model_id,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                )
            )

    @convert_to_dto
    async def get_usage(self, model_id: int) -> UsageDTO:
        return await self.usage_model_repo.get(
            filter=and_(
                Usage.user_id == self.context.user_id, Usage.model_id == model_id
            )
        )

    @convert_to_dto
    async def get_usages(self) -> List[UsageDTO]:
        return await self.usage_model_repo.get_all(
            filter=Usage.user_id == self.context.user_id
        )

    @convert_to_dto
    async def get_group_usages(self, model_id: int) -> List[UsageDTO]:
        # TODO: verify this subquery is correct
        return await self.usage_model_repo.get_all(
            joins=[(User, User.id == Usage.user_id)],
            filter=and_(
                Usage.model_id == model_id,
                User.group_name
                == select(User.group_name)
                .where(User.id == self.context.user_id)
                .scalar_subquery(),
            ),
        )

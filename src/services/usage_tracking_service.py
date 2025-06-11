from uuid import UUID
from litellm import Usage
from requests import Session
from sqlalchemy import select

from src.storage.models.usage import Usage as UsageModel


class UsageTrackingService:
    def __init__(self, db: Session):
        self.db = db

    async def track_usage(self, user_id: UUID, model_id: int, usage: Usage):
        results = await self.db.execute(
            select(UsageModel).where(UsageModel.user_id == user_id, UsageModel.model_id == model_id)
        )
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

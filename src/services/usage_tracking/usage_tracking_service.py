from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select

from src.services.common import errors
from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto
from src.services.usage_tracking.dto import AggregatedUsageItemDTO, BasicUsageDTO, UsageAggregationDTO, UsageDTO

from src.storage.base_repo import BaseRepository
from src.storage.models.ai_provider_model import AiProviderModel
from src.storage.models.usage import Usage
from src.storage.models.user import User


class UsageTrackingService:
    def __init__(self, context: Context, usage_model_repo: BaseRepository[Usage]):
        self.context = context
        self.usage_model_repo = usage_model_repo

    async def track_usage(self, user_id: UUID, model_id: int, usage: UsageDTO):
        existing_usage = await self.usage_model_repo.get(filter=and_(Usage.user_id == user_id, Usage.model_id == model_id))

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
        return await self.usage_model_repo.get(filter=and_(Usage.user_id == self.context.user_id, Usage.model_id == model_id))

    @convert_to_dto
    async def get_usages(self) -> List[UsageDTO]:
        return await self.usage_model_repo.select(filter=Usage.user_id == self.context.user_id)

    @convert_to_dto
    async def get_group_usages(self, model_id: int) -> List[UsageDTO]:
        # TODO: verify this subquery is correct
        return await self.usage_model_repo.select(
            joins=[(User, User.id == Usage.user_id)],
            filter=and_(
                Usage.model_id == model_id,
                User.group_name == select(User.group_name).where(User.id == self.context.user_id).scalar_subquery(),
            ),
        )

    async def get_aggregated_usage(
        self,
        aggregation: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[UUID] = None,
        model_id: Optional[int] = None,
    ) -> UsageAggregationDTO:
        filter_conditions = []
        if start_date:
            filter_conditions.append(Usage.created_at >= start_date)
        if end_date:
            filter_conditions.append(Usage.created_at <= end_date)
        if user_id:
            filter_conditions.append(Usage.user_id == user_id)
        if model_id:
            filter_conditions.append(Usage.model_id == model_id)

        filter_expr = and_(*filter_conditions) if filter_conditions else True

        columns_to_sum = [Usage.prompt_tokens, Usage.completion_tokens, Usage.total_tokens]

        total_result = await self.usage_model_repo.get_total(columns_to_sum=columns_to_sum, filter=filter_expr)

        total = BasicUsageDTO(
            prompt_tokens=total_result.get("prompt_tokens", 0) or 0,
            completion_tokens=total_result.get("completion_tokens", 0) or 0,
            total_tokens=total_result.get("total_tokens", 0) or 0,
        )

        if aggregation in ["minute", "hour", "day", "week", "month"]:
            period = aggregation
            date_trunc = func.date_trunc(period, Usage.created_at).label("date")

            select_columns = [
                date_trunc,
                func.sum(Usage.prompt_tokens).label("prompt_tokens"),
                func.sum(Usage.completion_tokens).label("completion_tokens"),
                func.sum(Usage.total_tokens).label("total_tokens"),
            ]

            results = await self.usage_model_repo.select(columns=select_columns, filter=filter_expr, group_by=[date_trunc], order_by=date_trunc, as_dict=True)

            data = [
                AggregatedUsageItemDTO(
                    date=item.get("date"),
                    prompt_tokens=item.get("prompt_tokens", 0),
                    completion_tokens=item.get("completion_tokens", 0),
                    total_tokens=item.get("total_tokens", 0),
                )
                for item in results
            ]

        elif aggregation == "model":
            select_columns = [
                Usage.model_id,
                AiProviderModel.name.label("model_name"),
                func.sum(Usage.prompt_tokens).label("prompt_tokens"),
                func.sum(Usage.completion_tokens).label("completion_tokens"),
                func.sum(Usage.total_tokens).label("total_tokens"),
            ]

            results = await self.usage_model_repo.select(
                columns=select_columns,
                joins=[(AiProviderModel, Usage.model_id == AiProviderModel.id)],
                filter=filter_expr,
                group_by=[Usage.model_id, AiProviderModel.name],
                as_dict=True,
            )

            data = [
                AggregatedUsageItemDTO(
                    model_id=item.get("model_id"),
                    model_name=item.get("model_name"),
                    prompt_tokens=item.get("prompt_tokens", 0),
                    completion_tokens=item.get("completion_tokens", 0),
                    total_tokens=item.get("total_tokens", 0),
                )
                for item in results
            ]

        elif aggregation == "user":
            select_columns = [
                Usage.user_id,
                User.email.label("user_email"),
                func.sum(Usage.prompt_tokens).label("prompt_tokens"),
                func.sum(Usage.completion_tokens).label("completion_tokens"),
                func.sum(Usage.total_tokens).label("total_tokens"),
            ]

            results = await self.usage_model_repo.select(
                columns=select_columns, joins=[(User, Usage.user_id == User.id)], filter=filter_expr, group_by=[Usage.user_id, User.email], as_dict=True
            )

            data = [
                AggregatedUsageItemDTO(
                    user_id=item.get("user_id"),
                    user_email=item.get("user_email"),
                    prompt_tokens=item.get("prompt_tokens", 0),
                    completion_tokens=item.get("completion_tokens", 0),
                    total_tokens=item.get("total_tokens", 0),
                )
                for item in results
            ]
        else:
            raise errors.InvalidInputError(f"Invalid aggregation type: {aggregation}")

        return UsageAggregationDTO(data=data, total=total)

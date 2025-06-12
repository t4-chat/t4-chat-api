from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ai_providers.ai_model_service import AiModelService
from src.services.context import Context
from src.services.inference.inference_service import InferenceService
from src.services.inference.models_shared.model_provider import ModelProvider
from src.services.usage_tracking_service import UsageTrackingService
from src.services.user_service import UserService
from src.storage.models.ai_provider_model import AiProviderModel
from src.storage.models.limits import Limits
from src.storage.models.user import User
from src.storage.models.user_group import UserGroup
from src.api.schemas.chat import ChatMessageResponse
from src.api.schemas.limits import UtilizationResponse, LimitResponse

from src.utils.enums import UserGroupType


class LimitsService:
    def __init__(
        self,
        context: Context,
        db: AsyncSession,
        usage_tracking_service: UsageTrackingService,
        inference_service: InferenceService,
        ai_model_service: AiModelService,
        user_service: UserService,
        model_provider: ModelProvider,
    ):
        self.context = context
        self.db = db

        self.usage_tracking_service = usage_tracking_service
        self.inference_service = inference_service
        self.ai_model_service = ai_model_service
        self.user_service = user_service
        self.model_provider = model_provider

    async def get_limits(self) -> List[LimitResponse]:
        results = await self.db.execute(select(Limits).join(Limits.user_groups).join(User, User.group_name == UserGroup.name).where(User.id == self.context.user_id))
        return [LimitResponse.model_validate(limit) for limit in results.scalars().all()]

    async def get_limits_by_model(self, model_id: int) -> LimitResponse:
        # for the given user with some group, and model, there is only one limit
        results = await self.db.execute(
            select(Limits).join(Limits.user_groups).join(User, User.group_name == UserGroup.name).where(User.id == self.context.user_id, Limits.model_id == model_id)
        )
        return LimitResponse.model_validate(results.scalar_one_or_none())

    async def _get_individual_utilization(self, model: AiProviderModel, limits: Limits, messages: Optional[List[ChatMessageResponse]] = None) -> UtilizationResponse:
        usage = await self.usage_tracking_service.get_usage(model.id)

        input_tokens = 0
        if messages:
            input_tokens = await self.model_provider.count_tokens(messages, model.provider, model)

        return UtilizationResponse(model_id=model.id, total_tokens=usage.prompt_tokens + input_tokens, percentage=(usage.prompt_tokens + input_tokens) / limits.max_tokens)

    async def _get_team_utilization(self, model: AiProviderModel, limits: Limits, messages: Optional[List[ChatMessageResponse]] = None) -> UtilizationResponse:
        group_usages = await self.usage_tracking_service.get_group_usages(model.id)
        total_tokens = sum(usage.total_tokens for usage in group_usages)

        input_tokens = 0
        if messages:
            input_tokens = await self.model_provider.count_tokens(messages, model.provider, model)

        return UtilizationResponse(model_id=model.id, total_tokens=total_tokens + input_tokens, percentage=(total_tokens + input_tokens) / limits.max_tokens)

    async def get_utilization(self, model_id: int, messages: Optional[List[ChatMessageResponse]] = None) -> UtilizationResponse:
        model = await self.ai_model_service.get_model(model_id)

        limits = await self.get_limits_by_model(model_id)

        user = await self.user_service.get_user_by_id(self.context.user_id, user_group=True)

        if user.user_group.type == UserGroupType.INDIVIDUAL:
            return await self._get_individual_utilization(model, limits, messages)
        elif user.user_group.type == UserGroupType.TEAM:
            return await self._get_team_utilization(model, limits, messages)

    async def get_utilizations(self) -> List[UtilizationResponse]:
        usages = await self.usage_tracking_service.get_usages()
        return [await self.get_utilization(usage.model_id) for usage in usages]

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_

from src.services.ai_providers.ai_model_service import AiModelService
from src.services.chats.dto import ChatMessageDTO
from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto
from src.services.common.enums import UserGroupType
from src.services.inference.inference_service import InferenceService
from src.services.inference.model_provider import ModelProvider
from src.services.limits.dto import LimitDTO, UtilizationDTO
from src.services.usage_tracking.usage_tracking_service import UsageTrackingService
from src.services.user.user_service import UserService

from src.services.ai_providers.dto import AiProviderModelDTO

from src.storage.base_repo import BaseRepository
from src.storage.models.limits import Limits
from src.storage.models.user import User
from src.storage.models.user_group import UserGroup


class LimitsService:
    def __init__(
        self,
        context: Context,
        limits_repo: BaseRepository[Limits],
        usage_tracking_service: UsageTrackingService,
        inference_service: InferenceService,
        ai_model_service: AiModelService,
        user_service: UserService,
        model_provider: ModelProvider,
    ):
        self.context = context
        self.limits_repo = limits_repo

        self.usage_tracking_service = usage_tracking_service
        self.inference_service = inference_service
        self.ai_model_service = ai_model_service
        self.user_service = user_service
        self.model_provider = model_provider

    @convert_to_dto
    async def get_limits(self) -> List[LimitDTO]:
        return await self.limits_repo.select(
            joins=[Limits.user_groups, (User, User.group_id == UserGroup.id)],
            filter=User.id == self.context.user_id,
        )

    @convert_to_dto
    async def get_limits_by_model(self, model_id: UUID) -> LimitDTO:
        results = await self.limits_repo.get(
            joins=[Limits.user_groups, (User, User.group_id == UserGroup.id)],
            filter=and_(User.id == self.context.user_id, Limits.model_id == model_id),
        )
        return results

    @convert_to_dto
    async def _get_individual_utilization(
        self,
        model: AiProviderModelDTO,
        limits: LimitDTO,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> UtilizationDTO:
        usage = await self.usage_tracking_service.get_usage(model.id)

        input_tokens = 0
        if messages:
            input_tokens = await self.model_provider.count_tokens(model, messages)

        return UtilizationDTO(
            model=model,
            total_tokens=usage.prompt_tokens + input_tokens,
            percentage=(usage.prompt_tokens + input_tokens) / limits.max_tokens,
        )

    async def _get_team_utilization(
        self,
        model: AiProviderModelDTO,
        limits: LimitDTO,
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> UtilizationDTO:
        group_usages = await self.usage_tracking_service.get_group_usages(model.id)
        total_tokens = sum(usage.total_tokens for usage in group_usages)

        input_tokens = 0
        if messages:
            input_tokens = await self.model_provider.count_tokens(model, messages)

        return UtilizationDTO(
            model=model,
            total_tokens=total_tokens + input_tokens,
            max_tokens=limits.max_tokens,
            percentage=(total_tokens + input_tokens) / limits.max_tokens,
        )

    async def get_utilization(self, model_id: UUID, messages: Optional[List[Dict[str, Any]]] = None) -> UtilizationDTO:
        model = await self.ai_model_service.get_model(model_id)

        limits = await self.get_limits_by_model(model_id)
        if not limits: # have no limits for this model, so we can't check utilization
            return UtilizationDTO(
                model=model,
                max_tokens=-1,
            )

        user = await self.user_service.get_user_by_id(self.context.user_id, user_group=True)

        if user.user_group.type == UserGroupType.INDIVIDUAL:
            return await self._get_individual_utilization(model, limits, messages)
        elif user.user_group.type == UserGroupType.TEAM:
            return await self._get_team_utilization(model, limits, messages)
        
    async def check_utilization(self, model_id: UUID, messages: Optional[List[Dict[str, Any]]] = None) -> bool:
        utilization = await self.get_utilization(model_id, messages)
        return utilization.percentage > 0.9

    async def get_utilizations(self) -> List[UtilizationDTO]:
        usages = await self.usage_tracking_service.get_usages()
        return [await self.get_utilization(usage.model_id) for usage in usages]

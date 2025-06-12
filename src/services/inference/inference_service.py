from typing import AsyncGenerator, Dict, List, Optional, Any

from fastapi import BackgroundTasks
import litellm
from sqlalchemy.ext.asyncio import AsyncSession


from src.services.budget_service import BudgetService
from src.services.context import Context
from src.services.errors import errors
from src.services.inference.config import DefaultResponseGenerationOptions
from src.services.inference.models.response_models import TextGenerationResponse, StreamGenerationResponse
from src.services.inference.models_shared import ModelProvider
from src.services.background_task_service import BackgroundTaskService

from src.storage.models.ai_provider import AiProvider
from src.storage.models.ai_provider_model import AiProviderModel
from src.storage.models.usage import Usage


class InferenceService:

    def __init__(
        self,
        context: Context,
        db: AsyncSession,
        models_provider: ModelProvider,
        background_task_service: BackgroundTaskService,
        budget_service: BudgetService,
    ):
        self._context = context
        self._db = db
        self._models_provider = models_provider
        self._background_task_service = background_task_service
        self._budget_service = budget_service

    async def _check_budget(self, model: AiProviderModel, usage: Usage) -> None:
        total_cost_usd = await self._models_provider.cost_per_token(model, usage)
        await self.budget_service.add_usage(total_cost_usd)

    async def _check_limits(self, model_id: int, messages: List[Dict[str, Any]]) -> None:
        utilization = await self.limits_service.get_utilization(model_id=model_id, messages=messages)
        if utilization.percentage >= 1.0:
            raise errors.LimitsExceededError(message=f"Limits exceeded for model {model_id}")

    async def generate_response(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        background_tasks: BackgroundTasks = None,
        **kwargs,
    ) -> TextGenerationResponse:
        resp = await self._models_provider.generate_response(
            provider=provider,
            model=model,
            messages=messages,
            options=options,
            **kwargs,
        )

        background_tasks.add_task(self._background_task_service.track_model_usage, user_id=self._context.user_id, model_id=model.id, usage=resp.usage)
        cost = await self._models_provider.cost_per_token(model, resp.usage)
        await self._budget_service.add_usage(usage=cost)

        return resp

    async def generate_response_stream(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptions] = None,
        background_tasks: BackgroundTasks = None,
        **kwargs,
    ) -> AsyncGenerator[StreamGenerationResponse, None]:
        usage = None
        async for chunk in self._models_provider.generate_response_stream(
            provider=provider,
            model=model,
            messages=messages,
            options=options,
            **kwargs,
        ):
            if chunk.usage:
                usage = chunk.usage
            yield chunk

        background_tasks.add_task(self._background_task_service.track_model_usage, user_id=self._context.user_id, model_id=model.id, usage=usage)
        cost = await self._models_provider.cost_per_token(model, usage)
        await self._budget_service.add_usage(usage=cost)

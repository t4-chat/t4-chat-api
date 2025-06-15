from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import BackgroundTasks

from src.services.background_tasks.background_task_service import BackgroundTaskService
from src.services.budget.budget_service import BudgetService
from src.services.common.context import Context
from src.services.inference.dto import DefaultResponseGenerationOptionsDTO, StreamGenerationDTO, TextGenerationDTO
from src.services.inference.model_provider import ModelProvider
from src.services.usage_tracking.dto import TokenUsageDTO

from src.services.ai_providers.dto import AiProviderModelDTO

from src.logging.logging_config import get_logger

logger = get_logger(__name__)


class InferenceService:
    def __init__(
        self,
        context: Context,
        models_provider: ModelProvider,
        background_task_service: BackgroundTaskService,
        budget_service: BudgetService,
    ):
        self._context = context
        self._models_provider = models_provider
        self._background_task_service = background_task_service
        self._budget_service = budget_service

    async def _ensure_budget(self, model: AiProviderModelDTO, usage: TokenUsageDTO) -> None:
        total_cost_usd = await self._models_provider.cost_per_token(model, usage)
        await self._budget_service.add_usage(total_cost_usd)

    async def generate_response(
        self,
        model: AiProviderModelDTO,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        background_tasks: BackgroundTasks = None,
        **kwargs,
    ) -> TextGenerationDTO:
        logger.info(f"Generating response for model: {model.name}, {model.id}, {model.slug}")
        
        resp = await self._models_provider.generate_response(
            model=model,
            messages=messages,
            options=options,
            **kwargs,
        )

        background_tasks.add_task(
            self._background_task_service.track_model_usage,
            user_id=self._context.user_id,
            model_id=model.id,
            usage=resp.usage,
        )
        await self._ensure_budget(model, resp.usage)
        
        logger.info(f"Generated response for model: {model.name}, {model.id}, {model.slug}")

        return resp

    async def generate_response_stream(
        self,
        model: AiProviderModelDTO,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        background_tasks: BackgroundTasks = None,
        **kwargs,
    ) -> AsyncGenerator[StreamGenerationDTO, None]:
        logger.info(f"Generating response stream for model: {model.name}, {model.id}, {model.slug}")
        
        usage = None
        async for chunk in self._models_provider.generate_response_stream(
            model=model,
            messages=messages,
            options=options,
            **kwargs,
        ):
            if chunk.usage:
                usage = chunk.usage
            yield chunk

        background_tasks.add_task(
            self._background_task_service.track_model_usage,
            user_id=self._context.user_id,
            model_id=model.id,
            usage=usage,
        )
        await self._ensure_budget(model, usage)
        
        logger.info(f"Generated response stream for model: {model.name}, {model.id}, {model.slug}")

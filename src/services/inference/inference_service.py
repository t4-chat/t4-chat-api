from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import BackgroundTasks

from src.services.background_tasks.background_task_service import BackgroundTaskService
from src.services.budget.budget_service import BudgetService
from src.services.common.context import Context
from src.services.inference.dto import DefaultResponseGenerationOptionsDTO, StreamGenerationDTO, TextGenerationDTO
from src.services.inference.model_provider import ModelProvider
from src.services.usage_tracking.dto import TokenUsageDTO

from src.services.ai_providers.dto import AiModelsModalitiesDTO, AiProviderModelDTO

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
        resp = await self._models_provider.generate_response(
            model=model,
            messages=messages,
            options=options,
            **kwargs,
        )

        # Track usage for each model separately
        for model_id, usage in resp.usage.items():
            background_tasks.add_task(
                self._background_task_service.track_model_usage,
                user_id=self._context.user_id,
                model_id=model_id,
                usage=usage,
            )

            # Ensure budget for each model - for single model case, should be the same model
            if model_id == model.id:
                await self._ensure_budget(model, usage)

        return resp

    async def generate_response_stream(
        self,
            models_modalities: AiModelsModalitiesDTO,
        messages: List[Dict[str, Any]],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        background_tasks: BackgroundTasks = None,
        **kwargs,
    ) -> AsyncGenerator[StreamGenerationDTO, None]:
        usage_by_model = None
        async for chunk in self._models_provider.generate_response_stream(
                models_modalities=models_modalities,
            messages=messages,
            options=options,
            **kwargs,
        ):
            if chunk.usage:
                usage_by_model = chunk.usage
            yield chunk

        # Track usage for each model separately
        if usage_by_model:
            for model_id, usage in usage_by_model.items():
                background_tasks.add_task(
                    self._background_task_service.track_model_usage,
                    user_id=self._context.user_id,
                    model_id=model_id,
                    usage=usage,
                )

                # Ensure budget for each model
                # Find the model DTO for budget calculation
                model_dto = None
                if model_id == models_modalities.llm.id:
                    model_dto = models_modalities.llm
                elif model_id == models_modalities.image_gen.id:
                    model_dto = models_modalities.image_gen

                if model_dto:
                    await self._ensure_budget(model_dto, usage)

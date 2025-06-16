from fastapi import BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ai_providers.ai_model_service import AiModelService
from src.services.background_tasks.background_task_service import BackgroundTaskService
from src.services.budget.budget_service import BudgetService
from src.services.chats.chat_service import ChatService
from src.services.chats.conversation_service import ConversationService
from src.services.chats.dto import ChatMessageDTO
from src.services.common.context import get_context, get_user_id
from src.services.files.cloud_storage_service import CloudStorageService
from src.services.files.files_service import FilesService
from src.services.inference.inference_service import InferenceService
from src.services.inference.model_provider import ModelProvider
from src.services.prompts.prompts_service import PromptsService

from src.storage.base_repo import BaseRepository
from src.storage.db import db_session_manager
from src.storage.models import AiProviderModel, Budget, Chat, ChatMessage, Resource, Limits, Usage

from src.api.schemas.chat import MultiModelCompletionRequestSchema


async def get_conversation_service(request: Request, db: AsyncSession) -> ConversationService:
    context = get_context(user_id=get_user_id(request))

    # Create repositories
    chat_repo = BaseRepository(Chat, db)
    chat_message_repo = BaseRepository(ChatMessage, db)
    ai_model_repo = BaseRepository(AiProviderModel, db)
    resource_repo = BaseRepository(Resource, db)
    budget_repo = BaseRepository(Budget, db)
    limits_repo = BaseRepository(Limits, db)
    usage_repo = BaseRepository(Usage, db)

    # Create dependent services
    cloud_storage_service = CloudStorageService(context=context)
    background_task_service = BackgroundTaskService(context=context)
    model_provider = ModelProvider(context=context)
    budget_service = BudgetService(context=context, budget_repo=budget_repo)

    # Create main services
    chat_service = ChatService(context=context, chat_repo=chat_repo, chat_message_repo=chat_message_repo)

    inference_service = InferenceService(context=context, models_provider=model_provider, background_task_service=background_task_service, budget_service=budget_service)

    prompts_service = PromptsService(context=context)

    files_service = FilesService(context=context, resource_repo=resource_repo, cloud_storage_service=cloud_storage_service)

    ai_model_service = AiModelService(context=context, ai_model_repo=ai_model_repo, limits_repo=limits_repo, usage_repo=usage_repo)

    return ConversationService(
        context=context,
        chat_service=chat_service,
        inference_service=inference_service,
        prompts_service=prompts_service,
        files_service=files_service,
        ai_model_service=ai_model_service,
    )


async def stream_conversation(request: Request, input: MultiModelCompletionRequestSchema, background_tasks: BackgroundTasks):
    async with db_session_manager.session() as db:
        conversation_service = await get_conversation_service(request, db)
        async for chunk in conversation_service.chat_completion_stream(
            model_ids=input.model_ids,
            message=ChatMessageDTO.model_validate(input.message),
            background_tasks=background_tasks,
        ):
            yield chunk

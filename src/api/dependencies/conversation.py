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
from src.services.host_api_keys.host_api_key_service import HostApiKeyService
from src.services.inference.inference_service import InferenceService
from src.services.inference.model_provider import ModelProvider
from src.services.inference.tools_service import ToolsService
from src.services.limits.limits_service import LimitsService
from src.services.prompts.prompts_service import PromptsService
from src.services.usage_tracking.usage_tracking_service import UsageTrackingService
from src.services.user.user_service import UserService

from src.storage.base_repo import BaseRepository
from src.storage.db import db_session_manager
from src.storage.models import AiProviderModel, Budget, Chat, ChatMessage, Limits, Resource, Usage, User
from src.storage.models.host_api_key import HostApiKey

from src.api.schemas.chat import MultiModelCompletionRequestSchema


async def get_conversation_service(request: Request, db: AsyncSession) -> ConversationService:
    context = get_context(user_id=get_user_id(request))

    # Create repositories
    user_repo = BaseRepository(User, db)
    chat_repo = BaseRepository(Chat, db)
    chat_message_repo = BaseRepository(ChatMessage, db)
    ai_model_repo = BaseRepository(AiProviderModel, db)
    resource_repo = BaseRepository(Resource, db)
    budget_repo = BaseRepository(Budget, db)
    limits_repo = BaseRepository(Limits, db)
    usage_repo = BaseRepository(Usage, db)
    host_api_key_repo = BaseRepository(HostApiKey, db)

    host_api_key_service = HostApiKeyService(context=context, host_api_key_repo=host_api_key_repo)

    # Create dependent services
    user_service = UserService(context=context, user_repo=user_repo)
    cloud_storage_service = CloudStorageService(context=context)
    background_task_service = BackgroundTaskService(context=context)
    tools_service = ToolsService(context=context)
    model_provider = ModelProvider(context=context, tools_service=tools_service, host_api_key_service=host_api_key_service)
    budget_service = BudgetService(context=context, budget_repo=budget_repo)
    usage_tracking_service = UsageTrackingService(context=context, usage_model_repo=usage_repo)

    # Create main services
    chat_service = ChatService(context=context, chat_repo=chat_repo, chat_message_repo=chat_message_repo)

    inference_service = InferenceService(context=context, models_provider=model_provider, background_task_service=background_task_service, budget_service=budget_service)

    prompts_service = PromptsService(context=context)

    files_service = FilesService(context=context, resource_repo=resource_repo, cloud_storage_service=cloud_storage_service)

    ai_model_service = AiModelService(context=context, ai_model_repo=ai_model_repo, limits_repo=limits_repo, usage_repo=usage_repo, host_api_key_service=host_api_key_service)

    limits_service = LimitsService(
        context=context,
        limits_repo=limits_repo,
        usage_tracking_service=usage_tracking_service,
        inference_service=inference_service,
        ai_model_service=ai_model_service,
        user_service=user_service,
        model_provider=model_provider,
    )

    return ConversationService(
        context=context,
        chat_service=chat_service,
        inference_service=inference_service,
        prompts_service=prompts_service,
        files_service=files_service,
        ai_model_service=ai_model_service,
        limits_service=limits_service,
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

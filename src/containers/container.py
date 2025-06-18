from typing import Annotated, Callable, Type, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.ai_providers.ai_model_host import AiModelHostService
from src.services.ai_providers.ai_model_service import AiModelService
from src.services.ai_providers.ai_provider_service import AiProviderService
from src.services.auth.auth_service import AuthService
from src.services.auth.token_service import TokenService
from src.services.background_tasks.background_task_service import BackgroundTaskService
from src.services.budget.budget_service import BudgetService
from src.services.chats.chat_service import ChatService
from src.services.chats.conversation_service import ConversationService
from src.services.common.context import Context, get_context
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
from src.storage.db import get_db_session
from src.storage.models import (
    AiProvider,
    AiProviderModel,
    Budget,
    Chat,
    ChatMessage,
    HostApiKey,
    Limits,
    Resource,
    Usage,
    User,
    WhiteList,
)
from src.storage.models.model_host import ModelHost
from src.storage.models.shared_conversation import SharedConversation
from src.storage.models.user_group import UserGroup

db = Annotated[AsyncSession, Depends(get_db_session)]

# Repositories
T = TypeVar("T")


def create_repo_factory(
    model_type: Type[T],
) -> Callable[[AsyncSession], BaseRepository[T]]:
    def get_repo(db: AsyncSession = Depends(get_db_session)) -> BaseRepository[T]:
        return BaseRepository(model_type, db)

    return get_repo


get_ai_model_repo = create_repo_factory(AiProviderModel)
get_user_repo = create_repo_factory(User)
get_ai_provider_repo = create_repo_factory(AiProvider)
get_resource_repo = create_repo_factory(Resource)
get_budget_repo = create_repo_factory(Budget)
get_limits_repo = create_repo_factory(Limits)
get_usage_model_repo = create_repo_factory(Usage)
get_chat_repo = create_repo_factory(Chat)
get_chat_message_repo = create_repo_factory(ChatMessage)
get_white_list_repo = create_repo_factory(WhiteList)
get_ai_model_host_repo = create_repo_factory(ModelHost)
get_user_group_repo = create_repo_factory(UserGroup)
get_shared_conversation_repo = create_repo_factory(SharedConversation)
get_host_api_key_repo = create_repo_factory(HostApiKey)


# Services
def get_tools_service(context: Context = Depends(get_context)) -> ToolsService:
    return ToolsService(context=context)


ToolsServiceDep = Annotated[ToolsService, Depends(get_tools_service)]


def get_host_api_key_service(
    context: Context = Depends(get_context),
    host_api_key_repo: BaseRepository[HostApiKey] = Depends(get_host_api_key_repo),
) -> HostApiKeyService:
    return HostApiKeyService(context=context, host_api_key_repo=host_api_key_repo)


HostApiKeyServiceDep = Annotated[HostApiKeyService, Depends(get_host_api_key_service)]


def get_cloud_storage_service(
    context: Context = Depends(get_context),
) -> CloudStorageService:
    return CloudStorageService(context=context)


CloudStorageServiceDep = Annotated[CloudStorageService, Depends(get_cloud_storage_service)]


def get_files_service(
        resource_repo: BaseRepository[Resource] = Depends(get_resource_repo),
        context: Context = Depends(get_context),
        cloud_storage_service: CloudStorageService = Depends(get_cloud_storage_service),
) -> FilesService:
    return FilesService(
        context=context,
        resource_repo=resource_repo,
        cloud_storage_service=cloud_storage_service,
    )


FilesServiceDep = Annotated[FilesService, Depends(get_files_service)]


def get_model_provider(
        context: Context = Depends(get_context),
        tools_service: ToolsService = Depends(get_tools_service),
        host_api_key_service: HostApiKeyService = Depends(get_host_api_key_service),
        files_service: FilesService = Depends(get_files_service),
) -> ModelProvider:
    return ModelProvider(context=context, tools_service=tools_service, host_api_key_service=host_api_key_service,
                         files_service=files_service)


ModelProviderServiceDep = Annotated[ModelProvider, Depends(get_model_provider)]


def get_prompts_service(context: Context = Depends(get_context)) -> PromptsService:
    return PromptsService(context=context)


PromptsServiceDep = Annotated[PromptsService, Depends(get_prompts_service)]


def get_background_task_service(
    context: Context = Depends(get_context),
) -> BackgroundTaskService:
    return BackgroundTaskService(context=context)


BackgroundTaskServiceDep = Annotated[BackgroundTaskService, Depends(get_background_task_service)]


def get_token_service() -> TokenService:
    return TokenService()


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def get_chat_service(
    chat_repo: BaseRepository[Chat] = Depends(get_chat_repo),
    chat_message_repo: BaseRepository[ChatMessage] = Depends(get_chat_message_repo),
    shared_conversation_repo: BaseRepository[SharedConversation] = Depends(get_shared_conversation_repo),
    context: Context = Depends(get_context),
) -> ChatService:
    return ChatService(context=context, chat_repo=chat_repo, chat_message_repo=chat_message_repo, shared_conversation_repo=shared_conversation_repo)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]


def get_ai_model_service(
    context: Context = Depends(get_context),
    ai_model_repo: BaseRepository[AiProviderModel] = Depends(get_ai_model_repo),
    limits_repo: BaseRepository[Limits] = Depends(get_limits_repo),
    usage_repo: BaseRepository[Usage] = Depends(get_usage_model_repo),
    host_api_key_service: HostApiKeyService = Depends(get_host_api_key_service),
) -> AiModelService:
    return AiModelService(
        context=context, ai_model_repo=ai_model_repo, limits_repo=limits_repo, usage_repo=usage_repo,
        host_api_key_service=host_api_key_service
    )


AiModelServiceDep = Annotated[AiModelService, Depends(get_ai_model_service)]


def get_budget_service(
    budget_repo: BaseRepository[Budget] = Depends(get_budget_repo),
    context: Context = Depends(get_context),
) -> BudgetService:
    return BudgetService(context=context, budget_repo=budget_repo)


BudgetServiceDep = Annotated[BudgetService, Depends(get_budget_service)]


def get_user_service(
    user_repo: BaseRepository[User] = Depends(get_user_repo),
    context: Context = Depends(get_context),
    user_group_repo: BaseRepository[UserGroup] = Depends(get_user_group_repo),
) -> UserService:
    return UserService(context=context, user_repo=user_repo, user_group_repo=user_group_repo)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_ai_provider_service(
    context: Context = Depends(get_context),
    ai_provider_repo: BaseRepository[AiProvider] = Depends(get_ai_provider_repo),
) -> AiProviderService:
    return AiProviderService(context=context, ai_provider_repo=ai_provider_repo)


AiProviderServiceDep = Annotated[AiProviderService, Depends(get_ai_provider_service)]


def get_usage_tracking_service(
    usage_model_repo: BaseRepository[Usage] = Depends(get_usage_model_repo),
    context: Context = Depends(get_context),
) -> UsageTrackingService:
    return UsageTrackingService(context=context, usage_model_repo=usage_model_repo)


UsageTrackingServiceDep = Annotated[UsageTrackingService, Depends(get_usage_tracking_service)]


def get_auth_service(
    token_service: TokenService = Depends(get_token_service),
    user_service: UserService = Depends(get_user_service),
    white_list_repo: BaseRepository[WhiteList] = Depends(get_white_list_repo),
) -> AuthService:
    return AuthService(token_service=token_service, user_service=user_service, white_list_repo=white_list_repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_inference_service(
    context: Context = Depends(get_context),
    model_provider: ModelProvider = Depends(get_model_provider),
    background_task_service: BackgroundTaskService = Depends(get_background_task_service),
    budget_service: BudgetService = Depends(get_budget_service),
) -> InferenceService:
    return InferenceService(
        context=context,
        models_provider=model_provider,
        background_task_service=background_task_service,
        budget_service=budget_service,
    )


InferenceServiceDep = Annotated[InferenceService, Depends(get_inference_service)]


def get_limits_service(
    limits_repo: BaseRepository[Limits] = Depends(get_limits_repo),
    context: Context = Depends(get_context),
    usage_tracking_service: UsageTrackingService = Depends(get_usage_tracking_service),
    inference_service: InferenceService = Depends(get_inference_service),
    ai_model_service: AiModelService = Depends(get_ai_model_service),
    user_service: UserService = Depends(get_user_service),
    model_provider: ModelProvider = Depends(get_model_provider),
) -> LimitsService:
    return LimitsService(
        context=context,
        limits_repo=limits_repo,
        usage_tracking_service=usage_tracking_service,
        inference_service=inference_service,
        ai_model_service=ai_model_service,
        user_service=user_service,
        model_provider=model_provider,
    )


LimitsServiceDep = Annotated[LimitsService, Depends(get_limits_service)]


def get_conversation_service(
    context: Context = Depends(get_context),
    chat_service: ChatService = Depends(get_chat_service),
    inference_service: InferenceService = Depends(get_inference_service),
    prompts_service: PromptsService = Depends(get_prompts_service),
    files_service: FilesService = Depends(get_files_service),
    ai_model_service: AiModelService = Depends(get_ai_model_service),
    limits_service: LimitsService = Depends(get_limits_service),
) -> ConversationService:
    return ConversationService(
        context=context,
        chat_service=chat_service,
        inference_service=inference_service,
        prompts_service=prompts_service,
        files_service=files_service,
        ai_model_service=ai_model_service,
        limits_service=limits_service,
    )


ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]


def get_ai_model_host_service(
    context: Context = Depends(get_context),
    ai_model_host_repo: BaseRepository[ModelHost] = Depends(get_ai_model_host_repo),
) -> AiModelHostService:
    return AiModelHostService(context=context, ai_model_host_repo=ai_model_host_repo)


AiModelHostServiceDep = Annotated[AiModelHostService, Depends(get_ai_model_host_service)]

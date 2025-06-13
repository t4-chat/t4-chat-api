from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from typing import Annotated

from src.services.ai_providers.ai_model_service import AiModelService
from src.services.ai_providers.ai_provider_service import AiProviderService
from src.services.auth.auth_service import AuthService
from src.services.auth.token_service import TokenService
from src.services.background_task_service import BackgroundTaskService
from src.services.budget_service import BudgetService
from src.services.chat_service import ChatService
from src.services.cloud_storage_service import CloudStorageService
from src.services.context import Context, get_context
from src.services.conversation_service import ConversationService
from src.services.files_service import FilesService
from src.services.inference.inference_service import InferenceService
from src.services.inference.models_shared.model_provider import ModelProvider
from src.services.limits_service import LimitsService
from src.services.prompts_service import PromptsService
from src.services.usage_tracking_service import UsageTrackingService
from src.services.user_service import UserService
from src.storage.database import get_db_session

db = Annotated[AsyncSession, Depends(get_db_session)]

def get_model_provider(context: Context = Depends(get_context)) -> ModelProvider:
    return ModelProvider(context=context)

model_provider_dep = Annotated[ModelProvider, Depends(get_model_provider)]

def get_cloud_storage_service(context: Context = Depends(get_context)) -> CloudStorageService:
    return CloudStorageService(context=context)

cloud_storage_service_dep = Annotated[CloudStorageService, Depends(get_cloud_storage_service)]

def get_prompts_service(context: Context = Depends(get_context)) -> PromptsService:
    return PromptsService(context=context)

prompts_service_dep = Annotated[PromptsService, Depends(get_prompts_service)]

def get_background_task_service(context: Context = Depends(get_context)) -> BackgroundTaskService:
    return BackgroundTaskService(context=context)

background_task_service_dep = Annotated[BackgroundTaskService, Depends(get_background_task_service)]

def get_token_service() -> TokenService:
    return TokenService()

token_service_dep = Annotated[TokenService, Depends(get_token_service)]

def get_chat_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context)
) -> ChatService:
    return ChatService(context=context, db=db)

chat_service_dep = Annotated[ChatService, Depends(get_chat_service)]

def get_ai_model_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context)
) -> AiModelService:
    return AiModelService(context=context, db=db)

ai_model_service_dep = Annotated[AiModelService, Depends(get_ai_model_service)]

def get_budget_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context)
) -> BudgetService:
    return BudgetService(context=context, db=db)

budget_service_dep = Annotated[BudgetService, Depends(get_budget_service)]

def get_user_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context)
) -> UserService:
    return UserService(context=context, db=db)

user_service_dep = Annotated[UserService, Depends(get_user_service)]

def get_ai_provider_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context)
) -> AiProviderService:
    return AiProviderService(context=context, db=db)

ai_provider_service_dep = Annotated[AiProviderService, Depends(get_ai_provider_service)]

def get_usage_tracking_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context)
) -> UsageTrackingService:
    return UsageTrackingService(context=context, db=db)

usage_tracking_service_dep = Annotated[UsageTrackingService, Depends(get_usage_tracking_service)]

def get_auth_service(
    db: AsyncSession = Depends(get_db_session),
    token_service: TokenService = Depends(get_token_service),
    user_service: UserService = Depends(get_user_service)
) -> AuthService:
    return AuthService(db=db, token_service=token_service, user_service=user_service)

auth_service_dep = Annotated[AuthService, Depends(get_auth_service)]

def get_files_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context),
    cloud_storage_service: CloudStorageService = Depends(get_cloud_storage_service)
) -> FilesService:
    return FilesService(context=context, db=db, cloud_storage_service=cloud_storage_service)

files_service_dep = Annotated[FilesService, Depends(get_files_service)]

def get_inference_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context),
    model_provider: ModelProvider = Depends(get_model_provider),
    background_task_service: BackgroundTaskService = Depends(get_background_task_service),
    budget_service: BudgetService = Depends(get_budget_service)
) -> InferenceService:
    return InferenceService(
        context=context,
        db=db,
        models_provider=model_provider,
        background_task_service=background_task_service,
        budget_service=budget_service
    )

inference_service_dep = Annotated[InferenceService, Depends(get_inference_service)]

def get_limits_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context),
    usage_tracking_service: UsageTrackingService = Depends(get_usage_tracking_service),
    inference_service: InferenceService = Depends(get_inference_service),
    ai_model_service: AiModelService = Depends(get_ai_model_service),
    user_service: UserService = Depends(get_user_service),
    model_provider: ModelProvider = Depends(get_model_provider)
) -> LimitsService:
    return LimitsService(
        context=context,
        db=db,
        usage_tracking_service=usage_tracking_service,
        inference_service=inference_service,
        ai_model_service=ai_model_service,
        user_service=user_service,
        model_provider=model_provider
    )

limits_service_dep = Annotated[LimitsService, Depends(get_limits_service)]

def get_conversation_service(
    db: AsyncSession = Depends(get_db_session),
    context: Context = Depends(get_context),
    chat_service: ChatService = Depends(get_chat_service),
    inference_service: InferenceService = Depends(get_inference_service),
    prompts_service: PromptsService = Depends(get_prompts_service),
    files_service: FilesService = Depends(get_files_service),
    ai_model_service: AiModelService = Depends(get_ai_model_service)
) -> ConversationService:
    return ConversationService(
        context=context,
        db=db,
        chat_service=chat_service,
        inference_service=inference_service,
        prompts_service=prompts_service,
        files_service=files_service,
        ai_model_service=ai_model_service
    )

conversation_service_dep = Annotated[ConversationService, Depends(get_conversation_service)]

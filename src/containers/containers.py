from dependency_injector import containers, providers
from src.containers.providers.settings import settings_provider
from src.containers.providers.database import db_provider
from src.services.user_service import UserService
from src.services.auth.token_service import TokenService
from src.services.auth.auth_service import AuthService
from src.services.usage_tracking_service import UsageTrackingService
from src.services.chat_service import ChatService
from src.services.inference.inference_service import InferenceService
from src.services.inference.models_shared.model_provider import ModelProvider
from src.services.ai_providers.ai_provider_service import AiProviderService
from src.services.ai_providers.ai_model_service import AiModelService
from src.services.background_task_service import BackgroundTaskService


class AppContainer(containers.DeclarativeContainer):
    # Add wiring configuration for all route modules
    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.api.routes.health_checks",
            "src.api.routes.ai_providers",
            "src.api.routes.chats",
            "src.api.routes.auth",
            "src.api.routes.users",
            "src.api.routes.ai_models",
        ]
    )

    # Configuration
    config = settings_provider

    # Resources
    db = db_provider

    # Model provider
    model_provider = providers.Factory(ModelProvider)

    # Services
    token_service = providers.Factory(TokenService)

    user_service = providers.Factory(UserService, db=db)

    auth_service = providers.Factory(AuthService, db=db, token_service=token_service, user_service=user_service)

    usage_tracking_service = providers.Factory(UsageTrackingService, db=db)
    
    background_task_service = providers.Singleton(BackgroundTaskService)

    inference_service = providers.Factory(
        InferenceService, 
        db=db, 
        models_provider=model_provider, 
        background_task_service=background_task_service
    )

    chat_service = providers.Factory(ChatService, db=db, inference_service=inference_service)

    ai_provider_service = providers.Factory(AiProviderService, db=db)

    ai_model_service = providers.Factory(AiModelService, db=db)

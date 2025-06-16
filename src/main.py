from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.storage.db import lifespan

from src.api.extensions.app_extensions import configure_openapi
from src.api.middleware.auth import create_auth_middleware
from src.api.middleware.errors import error_handling_middleware
from src.api.routes import ai_models, ai_providers, auth, chats, files, health_checks, host_api_keys, users, utilization
from src.api.routes.admin import admin_ai_models, admin_ai_models_hosts, admin_messages, admin_tools, admin_usage
from src.config import get_settings
from src.containers.container import get_token_service
from src.logging.logging_config import configure_logging, get_logger


def create_app():
    logger = get_logger(__name__)
    logger.info("Starting application...")

    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    app.include_router(health_checks.router)
    app.include_router(ai_providers.router)
    app.include_router(chats.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(admin_ai_models.router)
    app.include_router(admin_ai_models_hosts.router)
    app.include_router(admin_usage.router)
    app.include_router(ai_models.router)
    app.include_router(files.router)
    app.include_router(host_api_keys.router)
    app.include_router(utilization.router)
    app.include_router(admin_messages.router)
    app.include_router(admin_tools.router)

    configure_openapi(app)

    app.middleware("http")(error_handling_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(create_auth_middleware(get_token_service()))

    return app


configure_logging()
app = create_app()

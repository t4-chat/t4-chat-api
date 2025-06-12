from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.middleware.db_session import db_session_middleware

from src.api.routes import health_checks, ai_providers, chats, auth, users, ai_models, files, utilization
from src.api.middleware.auth import create_auth_middleware
from src.api.middleware.context import create_context_middleware
from src.api.middleware.errors import error_handling_middleware
from src.containers.containers import AppContainer
from src.logging.logging_config import configure_logging, get_logger

def create_app():
    logger = get_logger(__name__)
    logger.info('Starting application...')
    
    container = AppContainer()

    app = FastAPI(
        title=container.config().PROJECT_NAME,
        description=container.config().PROJECT_DESCRIPTION,
        version=container.config().VERSION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(create_context_middleware(container))
    app.middleware("http")(create_auth_middleware(container.token_service()))
    app.middleware("http")(db_session_middleware)
    app.middleware("http")(error_handling_middleware)

    app.include_router(health_checks.router)
    app.include_router(ai_providers.router)
    app.include_router(chats.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(ai_models.router)
    app.include_router(files.router)
    app.include_router(utilization.router)

    app.container = container
    
    return app

configure_logging()
app = create_app()

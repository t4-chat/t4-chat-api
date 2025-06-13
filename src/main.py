from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import health_checks, ai_providers, chats, auth, users, ai_models, files, utilization
from src.api.middleware.auth import create_auth_middleware
from src.api.middleware.errors import error_handling_middleware
from src.config import get_settings
from src.logging.logging_config import configure_logging, get_logger
from src.storage.database import db_session_manager
from src.services.auth.token_service import TokenService

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger(__name__)
    logger.info("Starting up database connection...")
    yield
    logger.info("Shutting down database connection...")
    if db_session_manager._engine is not None:
        await db_session_manager.close()

def create_app():
    logger = get_logger(__name__)
    logger.info('Starting application...')
    
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create an instance of TokenService for the auth middleware
    token_service_instance = TokenService()
    app.middleware("http")(create_auth_middleware(token_service_instance))
    app.middleware("http")(error_handling_middleware)

    app.include_router(health_checks.router)
    app.include_router(ai_providers.router)
    app.include_router(chats.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(ai_models.router)
    app.include_router(files.router)
    app.include_router(utilization.router)
    
    return app

configure_logging()
app = create_app()

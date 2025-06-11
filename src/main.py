from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.api.routes import health_checks, ai_providers, chats, auth, users, ai_models, files
from src.api.middleware.auth import create_auth_middleware
from src.containers.containers import AppContainer
from src.logging.logging_config import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Create and configure the container
container = AppContainer()

# Create the FastAPI application
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

app.middleware("http")(create_auth_middleware(container.token_service()))

app.include_router(health_checks.router)
app.include_router(ai_providers.router)
app.include_router(chats.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ai_models.router)
app.include_router(files.router)

app.container = container

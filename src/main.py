from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import health_checks, ai_providers, chats, auth, users, ai_models, files
from src.api.middleware.auth import create_auth_middleware
from src.api.middleware.context import ContextMiddleware
from src.api.middleware.errors import ErrorHandlingMiddleware
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

# Middleware is executed in reverse order of registration
# (last registered = first executed)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(ContextMiddleware, container=container)  # This middleware sets the context in the container
app.middleware("http")(create_auth_middleware(container.token_service()))

app.include_router(health_checks.router)
app.include_router(ai_providers.router)
app.include_router(chats.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ai_models.router)
app.include_router(files.router)

app.container = container

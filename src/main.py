from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import health_checks, ai_providers, chats, inference, auth, users
from src.api.middleware.auth import create_auth_middleware
from src.services.auth.token_service import get_token_service

app = FastAPI(
    title="Agg AI API",
    description="API for aggregating multiple AI providers",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(create_auth_middleware(get_token_service()))

app.include_router(health_checks.router)
app.include_router(ai_providers.router)
app.include_router(chats.router)
app.include_router(inference.router)
app.include_router(auth.router)
app.include_router(users.router)

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from src.api.routes import health_checks, ai_providers, chats, inference
from src.services.inference.setup import setup_inference_service

# Set up the inference service
setup_inference_service()

app = FastAPI(
    title="Agg AI API",
    description="API for aggregating multiple AI providers",
    version="0.1.0",
)

app.include_router(health_checks.router)
app.include_router(ai_providers.router)
app.include_router(chats.router)
app.include_router(inference.router)

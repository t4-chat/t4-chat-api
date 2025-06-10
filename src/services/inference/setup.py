import os

from src.services.inference.models_shared import ModelProvider
from src.services.inference.inference_service import InferenceService
from src.services.inference.providers import OpenAIProvider, AnthropicProvider


def setup_inference_service() -> None:
    service = InferenceService.get_instance()

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        service.register_provider(ModelProvider.OPENAI, OpenAIProvider(api_key=openai_api_key))

    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        service.register_provider(ModelProvider.ANTHROPIC, AnthropicProvider(api_key=anthropic_api_key))

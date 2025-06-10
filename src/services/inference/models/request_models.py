from typing import Optional

from pydantic import BaseModel

from src.services.inference.models_shared import ModelProvider
from src.services.inference.config import TextGenerationOptions


class TextGenerationRequest(BaseModel):
    """Request for text generation"""
    provider: ModelProvider
    model: str
    prompt: str
    options: Optional[TextGenerationOptions] = None 
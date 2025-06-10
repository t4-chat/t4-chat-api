from typing import Optional

from pydantic import BaseModel, Field

from src.services.inference.models_shared import ModelProvider
from src.services.inference.config import TextGenerationOptions


class TextGenerationRequest(BaseModel):
    """Request model for text generation"""
    provider: ModelProvider
    model: str
    prompt: str = Field(..., description="The input text prompt for generation")
    options: Optional[TextGenerationOptions] = None


class TextGenerationResponse(BaseModel):
    """Response model for text generation"""
    text: str = Field(..., description="The generated text response") 
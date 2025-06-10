from typing import Optional

from pydantic import BaseModel, Field

from src.services.inference.models_shared import ModelProvider
from src.services.inference.config import DefaultResponseGenerationOptions


class ResponseGenerationRequest(BaseModel):
    """Request model for text generation"""
    provider_id: int
    model_id: int
    prompt: str = Field(..., description="The input text prompt for generation")
    options: Optional[DefaultResponseGenerationOptions] = None


class ResponseGenerationResponse(BaseModel):
    """Response model for text generation"""
    text: str = Field(..., description="The generated text response") 
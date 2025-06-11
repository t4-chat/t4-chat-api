from typing import Optional

from pydantic import BaseModel, Field

from src.services.inference.models.response_models import Usage
from src.services.inference.models_shared import ModelProvider
from src.services.inference.config import DefaultResponseGenerationOptions


class ResponseGenerationRequest(BaseModel):
    provider_id: int
    model_id: int
    prompt: str = Field(..., description="The input text prompt for generation")
    options: Optional[DefaultResponseGenerationOptions] = None


class ResponseGenerationResponse(BaseModel):
    text: str = Field(..., description="The generated text response")
    usage: Usage = Field(..., description="The usage information for the generation")

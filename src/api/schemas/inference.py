from typing import List, Optional

from pydantic import BaseModel, Field


class UsageSchema(BaseModel):
    prompt_tokens: int = Field(..., description="The number of prompt tokens")
    completion_tokens: int = Field(..., description="The number of completion tokens")
    total_tokens: int = Field(..., description="The total number of tokens")


class ResponseGenerationRequest(BaseModel):
    provider_id: int = Field(..., description="The id of the provider")
    model_id: int = Field(..., description="The id of the model")
    prompt: str = Field(..., description="The input text prompt for generation")


class ResponseGenerationResponse(BaseModel):
    text: str = Field(..., description="The generated text response")
    usage: UsageSchema = Field(
        ..., description="The usage information for the generation"
    )

    class Config:
        from_attributes = True

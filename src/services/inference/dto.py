from typing import Optional

from pydantic import BaseModel

from src.services.usage_tracking.dto import TokenUsageDTO


class StreamGenerationDTO(BaseModel):
    text: str
    usage: Optional[TokenUsageDTO] = None


class TextGenerationDTO(BaseModel):
    text: str
    usage: TokenUsageDTO


class DefaultResponseGenerationOptionsDTO(BaseModel):
    temperature: float
    max_tokens: int

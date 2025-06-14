from typing import Optional

from pydantic import BaseModel, Field

from src.services.usage_tracking.dto import UsageDTO


class StreamGenerationDTO(BaseModel):
    text: str
    usage: Optional[UsageDTO] = None


class TextGenerationDTO(BaseModel):
    text: str
    usage: UsageDTO


class DefaultResponseGenerationOptionsDTO(BaseModel):
    temperature: float
    max_tokens: int

from typing import List, Optional

from pydantic import BaseModel

from src.services.usage_tracking.dto import TokenUsageDTO

class ThinkingContentDTO(BaseModel):
    type: Optional[str] = None
    thinking: Optional[str] = None
    signature: Optional[str] = None


class StreamGenerationDTO(BaseModel):
    text: Optional[str] = None
    usage: Optional[TokenUsageDTO] = None
    reasoning: Optional[str] = None
    thinking: Optional[List[ThinkingContentDTO]] = None


class TextGenerationDTO(BaseModel):
    text: str
    usage: TokenUsageDTO


class DefaultResponseGenerationOptionsDTO(BaseModel):
    temperature: float
    max_tokens: int

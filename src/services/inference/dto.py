from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from src.services.files.dto import FileDTO
from src.services.usage_tracking.dto import TokenUsageDTO


class ThinkingContentDTO(BaseModel):
    type: Optional[str] = None
    thinking: Optional[str] = None
    signature: Optional[str] = None


class StreamGenerationDTO(BaseModel):
    text: Optional[str] = None
    usage: Optional[Dict[UUID, TokenUsageDTO]] = None

    tools_calls: Optional[List[str]] = None

    attachments: Optional[List[FileDTO]] = None

    reasoning: Optional[str] = None
    thinking: Optional[List[ThinkingContentDTO]] = None


class TextGenerationDTO(BaseModel):
    text: str
    usage: Dict[UUID, TokenUsageDTO]


class DefaultResponseGenerationOptionsDTO(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    disable_tool_calls: Optional[bool] = None


class ToolCallResultDTO(BaseModel):
    content: Optional[Any] = None
    usage: Optional[TokenUsageDTO] = None

    error: Optional[Dict[str, Any]] = None


class ToolCallFunctionDTO(BaseModel):
    name: Optional[str] = None
    arguments: Optional[str] = None


class ToolCallDTO(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    function: Optional[ToolCallFunctionDTO] = None
    index: Optional[int] = None

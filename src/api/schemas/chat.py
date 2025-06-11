from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel

from src.services.inference.config import DefaultResponseGenerationOptions


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    attachments: Optional[List[str]] = None


class ChatMessages(BaseModel):
    messages: List[ChatMessage]


class ChatCompletionRequest(BaseModel):
    model_id: int
    messages: List[ChatMessage]

    chat_id: Optional[UUID] = None
    options: Optional[DefaultResponseGenerationOptions] = None


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatListItemResponse(BaseModel):
    id: UUID
    title: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    pinned: bool

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    id: UUID
    title: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    pinned: bool
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class StreamChunk(BaseModel):
    type: str  # "content" or "done"
    content: Optional[str] = None


class UpdateChatTitleRequest(BaseModel):
    title: str

from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID
from pydantic import BaseModel

from src.services.inference.config import DefaultResponseGenerationOptions

class ChatMessageRequest(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    attachments: Optional[List[UUID]] = None

class ChatMessageResponse(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    attachments: Optional[List[UUID]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatCompletionRequest(BaseModel):
    model_id: int
    messages: List[ChatMessageRequest]

    chat_id: Optional[UUID] = None
    options: Optional[DefaultResponseGenerationOptions] = None


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

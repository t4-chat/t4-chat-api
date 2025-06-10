from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from src.services.inference.config import DefaultResponseGenerationOptions


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion"""

    messages: List[dict] = []  # List of message objects with role and content
    provider_id: int
    model_id: int
    options: Optional[DefaultResponseGenerationOptions] = None
    chat_id: Optional[UUID] = None


class ChatMessageResponse(BaseModel):
    """Response model for a chat message"""

    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Response model for a chat"""

    id: UUID
    title: str
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class StreamChunk(BaseModel):
    """Streaming chunk response"""

    type: str  # "content" or "done"
    content: Optional[str] = None

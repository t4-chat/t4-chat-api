from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatMessageDTO(BaseModel):
    id: Optional[UUID] = None
    
    chat_id: Optional[UUID] = None
    model_id: Optional[int] = None # None for user messages
    
    role: Optional[Literal["user", "assistant"]] = None
    content: Optional[str] = None
    attachments: Optional[List[UUID]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatDTO(BaseModel):
    id: UUID
    title: Optional[str]
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    pinned: bool
    messages: List[ChatMessageDTO] = []

    class Config:
        from_attributes = True

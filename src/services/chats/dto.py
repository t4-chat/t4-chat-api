from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatMessageDTO(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    attachments: Optional[List[UUID]] = None
    created_at: datetime

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

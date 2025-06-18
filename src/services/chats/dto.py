from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageDTO(BaseModel):
    id: Optional[UUID] = None
    
    chat_id: Optional[UUID] = None
    model_id: Optional[UUID] = None
    image_gen_model_id: Optional[UUID] = None
    previous_message_id: Optional[UUID] = None
    seq_num: Optional[int] = None
    
    role: Optional[Literal["user", "assistant"]] = None
    content: Optional[str] = None
    selected: Optional[bool] = None
    attachments: Optional[List[UUID]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SharedConversationDTO(BaseModel):
    id: UUID

    class Config:
        from_attributes = True


class ChatDTO(BaseModel):
    id: UUID
    title: Optional[str]
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    pinned: bool
    shared_conversation: Optional[SharedConversationDTO] = None
    messages: List[ChatMessageDTO] = []

    class Config:
        from_attributes = True


class SharedConversationListItemDTO(BaseModel):
    id: UUID
    created_at: datetime
    chat: ChatDTO

    class Config:
        from_attributes = True


class CompletionOptionsRequestDTO(BaseModel):
    tools: List[str] = Field(..., description="The tools to use for the completion")

    class Config:
        from_attributes = True
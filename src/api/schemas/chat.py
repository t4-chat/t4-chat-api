from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.services.inference.dto import DefaultResponseGenerationOptionsDTO


class ChatMessageRequestSchema(BaseModel):
    role: Literal["user", "assistant"] = Field(
        ..., description="The role of the message"
    )
    content: str = Field(..., description="The content of the message")
    attachments: Optional[List[UUID]] = Field(
        None, description="The attachments of the message"
    )


class ChatMessageResponseSchema(BaseModel):
    id: UUID
    role: Literal["user", "assistant"] = Field(
        ..., description="The role of the message"
    )
    content: str = Field(..., description="The content of the message")
    attachments: Optional[List[UUID]] = Field(
        None, description="The attachments of the message"
    )
    created_at: datetime = Field(..., description="The creation date of the message")

    class Config:
        from_attributes = True


class ChatCompletionRequestSchema(BaseModel):
    model_id: int = Field(..., description="The id of the model")
    messages: List[ChatMessageRequestSchema] = Field(
        ..., description="The messages of the chat"
    )

    chat_id: Optional[UUID] = Field(None, description="The id of the chat")
    options: Optional[DefaultResponseGenerationOptionsDTO] = Field(
        None, description="The options of the chat"
    )


class ChatListItemResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the chat")
    title: str = Field(..., description="The title of the chat")
    user_id: UUID = Field(..., description="The id of the user")
    created_at: datetime = Field(..., description="The creation date of the chat")
    updated_at: datetime = Field(..., description="The update date of the chat")
    pinned: bool = Field(..., description="Whether the chat is pinned")

    class Config:
        from_attributes = True


class ChatResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the chat")
    title: str = Field(..., description="The title of the chat")
    user_id: UUID = Field(..., description="The id of the user")
    created_at: datetime = Field(..., description="The creation date of the chat")
    updated_at: datetime = Field(..., description="The update date of the chat")
    pinned: bool = Field(..., description="Whether the chat is pinned")
    messages: List[ChatMessageResponseSchema] = Field(
        ..., description="The messages of the chat"
    )

    class Config:
        from_attributes = True


class StreamChunkSchema(BaseModel):
    type: str = Field(..., description="The type of the chunk")
    content: Optional[str] = Field(None, description="The content of the chunk")


class UpdateChatTitleRequestSchema(BaseModel):
    title: str = Field(..., description="The title of the chat")

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageRequestSchema(BaseModel):
    id: Optional[UUID] = Field(None, description="The id of the message")

    chat_id: Optional[UUID] = Field(None, description="The id of the chat")

    content: str = Field(..., description="The content of the message")
    attachments: Optional[List[UUID]] = Field(None, description="The attachments of the message")


class ChatMessageResponseSchema(BaseModel):
    id: UUID

    role: Literal["user", "assistant"] = Field(..., description="The role of the message")
    content: str = Field(..., description="The content of the message")
    selected: Optional[bool] = Field(None, description="Whether the message is selected")
    model_id: Optional[int] = Field(None, description="The id of the model")

    attachments: Optional[List[UUID]] = Field(None, description="The attachments of the message")
    previous_message_id: Optional[UUID] = Field(None, description="The ID of the previous message in the conversation chain")
    created_at: datetime = Field(..., description="The creation date of the message")

    class Config:
        from_attributes = True


class ChatMessagesResponseSchema(BaseModel):
    messages: List[ChatMessageResponseSchema] = Field(..., description="The messages of the chat")

    class Config:
        from_attributes = True


class MultiModelCompletionRequestSchema(BaseModel):
    model_ids: List[int] = Field(..., description="The ids of the models to compare (minimum 2)")
    message: ChatMessageRequestSchema = Field(..., description="The message of the chat")


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
    messages: List[ChatMessageResponseSchema] = Field(..., description="The messages of the chat")

    class Config:
        from_attributes = True


class StreamChunkSchema(BaseModel):
    type: str = Field(..., description="The type of the chunk")
    content: Optional[str] = Field(None, description="The content of the chunk")


class UpdateChatTitleRequestSchema(BaseModel):
    title: str = Field(..., description="The title of the chat")

class DeleteChatsRequestSchema(BaseModel):
    chat_ids: List[UUID] = Field(..., description="The ids of the chats to delete")

from datetime import datetime
from typing import Dict, List, Literal, Optional
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
    model_id: Optional[UUID] = Field(None, description="The id of the model")

    attachments: Optional[List[UUID]] = Field(None, description="The attachments of the message")
    previous_message_id: Optional[UUID] = Field(None, description="The ID of the previous message in the conversation chain")
    created_at: datetime = Field(..., description="The creation date of the message")

    class Config:
        from_attributes = True


class ChatMessagesResponseSchema(BaseModel):
    messages: List[ChatMessageResponseSchema] = Field(..., description="The messages of the chat")

    class Config:
        from_attributes = True


class AiModelsRequestSchema(BaseModel):
    image_gen_model_id: Optional[UUID] = Field(None, description="The id of the image generation model")


class CompletionOptionsRequestSchema(BaseModel):
    tools: List[str] = Field([], description="The tools to use for the completion")


class MultiModelCompletionRequestSchema(BaseModel):
    model_ids: List[UUID] = Field(..., description="The ids of the models to compare (minimum 2)")
    models_auxiliary: Optional[Dict[UUID, AiModelsRequestSchema]] = Field(None,
                                                                          description="The auxiliary models to use for the chat")
    message: ChatMessageRequestSchema = Field(..., description="The message of the chat")
    shared_conversation_id: Optional[UUID] = Field(None, description="The id of the shared conversation")
    options: Optional[CompletionOptionsRequestSchema] = Field(None, description="The options for the completion")


class SharedConversationResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the shared conversation")

    class Config:
        from_attributes = True


class ChatListItemResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the chat")
    title: str = Field(..., description="The title of the chat")
    user_id: UUID = Field(..., description="The id of the user")
    created_at: datetime = Field(..., description="The creation date of the chat")
    updated_at: datetime = Field(..., description="The update date of the chat")
    pinned: bool = Field(..., description="Whether the chat is pinned")
    shared_conversation: Optional[SharedConversationResponseSchema] = Field(None, description="The shared conversation")

    class Config:
        from_attributes = True


class ChatResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the chat")
    title: str = Field(..., description="The title of the chat")
    user_id: UUID = Field(..., description="The id of the user")
    created_at: datetime = Field(..., description="The creation date of the chat")
    updated_at: datetime = Field(..., description="The update date of the chat")
    pinned: bool = Field(..., description="Whether the chat is pinned")
    shared_conversation: Optional[SharedConversationResponseSchema] = Field(None, description="The shared conversation")
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


class UnshareChatsRequestSchema(BaseModel):
    shared_conversation_ids: List[UUID] = Field(..., description="The ids of the shared conversations to unshare")


class ShareChatResponseSchema(BaseModel):
    shared_conversation_id: UUID = Field(..., description="The id of the shared conversation")


class SharedConversationChatResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the chat")
    title: str = Field(..., description="The title of the chat")
    

class SharedConversationListItemResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the shared conversation")
    created_at: datetime = Field(..., description="The creation date of the shared conversation")
    chat: SharedConversationChatResponseSchema = Field(..., description="The shared chat information")

    class Config:
        from_attributes = True
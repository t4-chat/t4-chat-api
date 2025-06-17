from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.api.dependencies.budget import check_budget
from src.api.dependencies.conversation import stream_conversation
from src.api.schemas.chat import (
    ChatListItemResponseSchema,
    ChatMessageResponseSchema,
    ChatMessagesResponseSchema,
    ChatResponseSchema,
    DeleteChatsRequestSchema,
    MultiModelCompletionRequestSchema,
    ShareChatResponseSchema,
    UnshareChatsRequestSchema,
    UpdateChatTitleRequestSchema,
)
from src.containers.container import ChatServiceDep

router = APIRouter(prefix="/api/chats", tags=["Chats"])


@router.post("", response_model=ChatResponseSchema)
async def create_chat(chat_service: ChatServiceDep):
    return await chat_service.create_chat()


@router.get("", response_model=List[ChatListItemResponseSchema])
async def get_chats(chat_service: ChatServiceDep):
    return await chat_service.get_user_chats()


@router.get("/{chat_id}", response_model=ChatResponseSchema)
async def get_chat(chat_id: UUID, chat_service: ChatServiceDep):
    chat = await chat_service.get_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("")
async def delete_chats(delete_chats_request: DeleteChatsRequestSchema, chat_service: ChatServiceDep):
    await chat_service.delete_chats(chat_ids=delete_chats_request.chat_ids)
    return {"status": "success"}


@router.get("/{chat_id}/messages", response_model=ChatMessagesResponseSchema)
async def get_messages(chat_id: UUID, chat_service: ChatServiceDep):
    messages = await chat_service.get_messages(chat_id=chat_id)
    return ChatMessagesResponseSchema(messages=messages)


@router.post("/conversation", response_class=StreamingResponse)
async def send_message(message: MultiModelCompletionRequestSchema, background_tasks: BackgroundTasks, request: Request, _: bool = Depends(check_budget)):
    return StreamingResponse(
        stream_conversation(request, message, background_tasks),
        media_type="text/event-stream",
    )


@router.patch("/{chat_id}/title")
async def update_chat_title(chat_id: UUID, request: UpdateChatTitleRequestSchema, chat_service: ChatServiceDep):
    return await chat_service.update_chat_title(chat_id=chat_id, title=request.title)


@router.patch("/{chat_id}/pin")
async def pin_chat(chat_id: UUID, chat_service: ChatServiceDep):
    return await chat_service.pin_chat(chat_id=chat_id)


@router.patch("/{chat_id}/messages/{message_id}/select", response_model=ChatMessageResponseSchema)
async def select_message(chat_id: UUID, message_id: UUID, chat_service: ChatServiceDep):
    return await chat_service.select_message(chat_id=chat_id, message_id=message_id)


@router.post("/{chat_id}/share", response_model=ShareChatResponseSchema)
async def share_chat(chat_id: UUID, chat_service: ChatServiceDep):
    shared_conversation_id = await chat_service.share_chat(chat_id=chat_id)
    return ShareChatResponseSchema(shared_conversation_id=shared_conversation_id)


@router.get("/shared/{shared_conversation_id}", response_model=ChatResponseSchema)
async def get_shared_chat(shared_conversation_id: UUID, chat_service: ChatServiceDep):
    chat = await chat_service.get_shared_chat(shared_conversation_id=shared_conversation_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/share")
async def unshare_chats(unshare_chats_request: UnshareChatsRequestSchema, chat_service: ChatServiceDep):
    await chat_service.unshare_chats(shared_conversation_ids=unshare_chats_request.shared_conversation_ids)
    return {"status": "success"}
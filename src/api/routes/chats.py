from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.api.dependencies.budget import check_budget
from src.api.dependencies.conversation import stream_conversation
from src.api.schemas.chat import (
    ChatCompletionRequestSchema,
    ChatListItemResponseSchema,
    ChatMessagesResponseSchema,
    ChatResponseSchema,
    UpdateChatTitleRequestSchema,
)
from src.containers.container import ChatServiceDep

router = APIRouter(prefix="/api/chats", tags=["chats"])


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


@router.delete("/{chat_id}")
async def delete_chat(chat_id: UUID, chat_service: ChatServiceDep):
    success = await chat_service.delete_chat(chat_id=chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "message": "Chat deleted"}


@router.get("/{chat_id}/messages", response_model=ChatMessagesResponseSchema)
async def get_messages(chat_id: UUID, chat_service: ChatServiceDep):
    messages = await chat_service.get_messages(chat_id=chat_id)
    return ChatMessagesResponseSchema(messages=messages)


@router.post("/conversation", response_class=StreamingResponse)
async def send_message(
    message: ChatCompletionRequestSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    _: bool = Depends(check_budget)
):
    return StreamingResponse(
        stream_conversation(request, message, background_tasks),
        media_type="text/event-stream",
    )


@router.patch("/{chat_id}/title")
async def update_chat_title(
    chat_id: UUID, request: UpdateChatTitleRequestSchema, chat_service: ChatServiceDep
):
    return await chat_service.update_chat_title(chat_id=chat_id, title=request.title)


@router.patch("/{chat_id}/pin")
async def pin_chat(chat_id: UUID, chat_service: ChatServiceDep):
    return await chat_service.pin_chat(chat_id=chat_id)

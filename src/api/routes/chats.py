from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Body, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from src.api.schemas.chat import ChatResponse, ChatCompletionRequest, UpdateChatTitleRequest, ChatListItemResponse
from src.containers.container import chat_service_dep, conversation_service_dep
from src.api.dependencies.budget import check_budget


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("", response_model=ChatResponse)
async def create_chat(chat_service: chat_service_dep):
    chat = await chat_service.create_chat()
    return chat


@router.get("", response_model=List[ChatListItemResponse])
async def get_chats(chat_service: chat_service_dep):
    return await chat_service.get_user_chats()


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: UUID, chat_service: chat_service_dep):
    chat = await chat_service.get_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
async def delete_chat(chat_id: UUID, chat_service: chat_service_dep):
    success = await chat_service.delete_chat(chat_id=chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "message": "Chat deleted"}


@router.post("/conversation", response_class=StreamingResponse)
async def send_message(
    message: ChatCompletionRequest,
    conversation_service: conversation_service_dep,
    background_tasks: BackgroundTasks,
    _: bool = Depends(check_budget),
):
    return StreamingResponse(
        conversation_service.chat_completion_stream(
            chat_id=message.chat_id,
            model_id=message.model_id,
            messages=message.messages,
            options=message.options,
            background_tasks=background_tasks,
        ),
        media_type="text/event-stream",
    )


@router.patch("/{chat_id}/title")
async def update_chat_title(chat_id: UUID, request: UpdateChatTitleRequest, chat_service: chat_service_dep):
    chat = await chat_service.update_chat_title(chat_id=chat_id, title=request.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/{chat_id}/pin")
async def pin_chat(chat_id: UUID, chat_service: chat_service_dep):
    chat = await chat_service.pin_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

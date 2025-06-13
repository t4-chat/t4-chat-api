from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Body, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from src.api.schemas.chat import ChatResponse, ChatCompletionRequest, UpdateChatTitleRequest, ChatListItemResponse
from src.containers.di import chat_service, conversation_service
from src.api.dependencies.budget import check_budget


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("", response_model=ChatResponse)
async def create_chat(service: chat_service):
    chat = await service.create_chat()
    return chat


@router.get("", response_model=List[ChatListItemResponse])
async def get_chats(service: chat_service):
    return await service.get_user_chats()


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: UUID, service: chat_service):
    chat = await service.get_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
async def delete_chat(chat_id: UUID, service: chat_service):
    success = await service.delete_chat(chat_id=chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "message": "Chat deleted"}


@router.post("/conversation", response_class=StreamingResponse)
async def send_message(
    message: ChatCompletionRequest,
    conv_service: conversation_service,
    background_tasks: BackgroundTasks,
    _: bool = Depends(check_budget),
):
    return StreamingResponse(
        conv_service.chat_completion_stream(
            chat_id=message.chat_id,
            model_id=message.model_id,
            messages=message.messages,
            options=message.options,
            background_tasks=background_tasks,
        ),
        media_type="text/event-stream",
    )


@router.patch("/{chat_id}/title")
async def update_chat_title(chat_id: UUID, request: UpdateChatTitleRequest, service: chat_service):
    chat = await service.update_chat_title(chat_id=chat_id, title=request.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/{chat_id}/pin")
async def pin_chat(chat_id: UUID, service: chat_service):
    chat = await service.pin_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

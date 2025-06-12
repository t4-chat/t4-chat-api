from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Body, Request, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject, Provide

from src.api.schemas.chat import ChatResponse, ChatCompletionRequest, UpdateChatTitleRequest, ChatListItemResponse
from src.services.chat_service import ChatService
from src.containers.containers import AppContainer
from src.api.dependencies.budget import check_budget


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse)
@inject
async def create_chat(service: ChatService = Depends(Provide[AppContainer.chat_service])):
    chat = await service.create_chat()
    return chat


@router.get("/", response_model=List[ChatListItemResponse])
@inject
async def get_chats(service: ChatService = Depends(Provide[AppContainer.chat_service])):
    return await service.get_user_chats()


@router.get("/{chat_id}", response_model=ChatResponse)
@inject
async def get_chat(chat_id: UUID, service: ChatService = Depends(Provide[AppContainer.chat_service])):
    chat = await service.get_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
@inject
async def delete_chat(chat_id: UUID, service: ChatService = Depends(Provide[AppContainer.chat_service])):
    success = await service.delete_chat(chat_id=chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "message": "Chat deleted"}


@router.post("/conversation", response_class=StreamingResponse)
@inject
async def send_message(
    message: ChatCompletionRequest = Body(...),
    chat_service: ChatService = Depends(Provide[AppContainer.chat_service]),
    background_tasks: BackgroundTasks = None,
    _: bool = Depends(check_budget),
):
    return StreamingResponse(
        chat_service.chat_completion_stream(
            chat_id=message.chat_id,
            model_id=message.model_id,
            messages=message.messages,
            options=message.options,
            background_tasks=background_tasks,
        ),
        media_type="text/event-stream",
    )


@router.patch("/{chat_id}/title")
@inject
async def update_chat_title(chat_id: UUID, request: UpdateChatTitleRequest, service: ChatService = Depends(Provide[AppContainer.chat_service])):
    chat = await service.update_chat_title(chat_id=chat_id, title=request.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/{chat_id}/pin")
@inject
async def pin_chat(chat_id: UUID, service: ChatService = Depends(Provide[AppContainer.chat_service])):
    chat = await service.pin_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Body, Request, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject, Provide

from src.api.models.chat import ChatResponse, ChatCompletionRequest, UpdateChatTitleRequest
from src.services.chat_service import ChatService
from src.containers.containers import AppContainer


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse)
@inject
async def create_chat(
    request: Request, 
    service: ChatService = Depends(Provide[AppContainer.chat_service])
):
    user_id = request.state.user_id
    chat = service.create_chat(user_id=user_id)
    return chat


@router.get("/", response_model=List[ChatResponse])
@inject
async def get_chats(
    request: Request, 
    service: ChatService = Depends(Provide[AppContainer.chat_service])
):
    user_id = request.state.user_id
    return service.get_user_chats(user_id=user_id)


@router.get("/{chat_id}", response_model=ChatResponse)
@inject
async def get_chat(
    chat_id: UUID, 
    service: ChatService = Depends(Provide[AppContainer.chat_service])
):
    chat = service.get_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
@inject
async def delete_chat(
    chat_id: UUID, 
    service: ChatService = Depends(Provide[AppContainer.chat_service])
):
    success = service.delete_chat(chat_id=chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "message": "Chat deleted"}

@router.post("/conversation", response_class=StreamingResponse)
@inject
async def send_message(
    request: Request,
    message: ChatCompletionRequest = Body(...),
    chat_service: ChatService = Depends(Provide[AppContainer.chat_service]),
    background_tasks: BackgroundTasks = None,
):
    user_id = request.state.user_id
    return StreamingResponse(
        chat_service.chat_completion_stream(
            user_id=user_id,
            messages=message.messages,
            model_id=message.model_id,
            options=message.options,
            chat_id=message.chat_id,
            background_tasks=background_tasks,
        ), 
        media_type="text/event-stream"
    )

@router.patch("/{chat_id}/title")
@inject
async def update_chat_title(
    chat_id: UUID, 
    request: UpdateChatTitleRequest, 
    service: ChatService = Depends(Provide[AppContainer.chat_service])
):
    chat = service.update_chat_title(chat_id=chat_id, title=request.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@router.patch("/{chat_id}/pin")
@inject
async def pin_chat(
    chat_id: UUID, 
    service: ChatService = Depends(Provide[AppContainer.chat_service])
):
    chat = service.pin_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


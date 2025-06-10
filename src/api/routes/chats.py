import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse

from src.api.models.chat import ChatResponse, ChatCompletionRequest, StreamChunk
from src.services import chat_service


router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("/", response_model=ChatResponse)
async def create_chat(title: str, service: chat_service):
    """Create a new chat"""
    # For demo, using a fixed user ID
    user_id = UUID('123e4567-e89b-12d3-a456-426614174000')
    chat = service.create_chat(user_id=user_id, title=title)
    return chat


@router.get("/", response_model=List[ChatResponse])
async def get_chats(service: chat_service):
    """Get all chats for the current user"""
    # For demo, using a fixed user ID
    user_id = UUID('123e4567-e89b-12d3-a456-426614174000')
    return service.get_user_chats(user_id=user_id)


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: UUID, service: chat_service):
    """Get a chat by ID"""
    chat = service.get_chat(chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
async def delete_chat(chat_id: UUID, service: chat_service):
    """Delete a chat"""
    success = service.delete_chat(chat_id=chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success", "message": "Chat deleted"}


@router.post("/{chat_id}/messages", response_class=StreamingResponse)
async def send_message(
    chat_id: UUID, 
    chat_service: chat_service,
    message: ChatCompletionRequest = Body(...)
):
    """Send a message to a chat and get a streaming response"""

    async def stream_response():
        async for chunk in chat_service.chat_completion_stream(
            chat_id=chat_id,
            messages=message.messages,
            provider=message.provider,
            model=message.model,
            options=message.options
        ):
            # Format as server-sent event
            data = {
                "type": "content",
                "text": chunk
            }
            yield f"data: {json.dumps(data)}\n\n"
        
        # Send completion event
        yield f"data: {json.dumps({"type": "done"})}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")

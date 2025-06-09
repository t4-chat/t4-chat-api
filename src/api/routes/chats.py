from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json

router = APIRouter(
    prefix="/api/chats",
    tags=["chats"]
)

class ChatMessage(BaseModel):
    message: str

async def fake_stream_response(message: str):
    # Simulate AI thinking and generating response
    response_parts = [
        "I'm thinking about",
        " your message regarding",
        f" '{message}'...",
        "\nHere's my response:",
        "\nThis is a mock streaming",
        " response that simulates",
        " real AI behavior",
        " with delays between chunks."
    ]
    
    for part in response_parts:
        # Create SSE formatted data
        data = json.dumps({"content": part, "type": "content"})
        yield f"data: {data}\n\n"
        await asyncio.sleep(0.5)  # Add delay between chunks
    
    # Send done event
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

@router.post("/messages")
async def stream_chat_response(message: ChatMessage):
    return StreamingResponse(
        fake_stream_response(message.message),
        media_type="text/event-stream"
    )

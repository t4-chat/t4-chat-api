import asyncio
import json
from typing import Annotated, AsyncGenerator, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.services.inference import InferenceService, ModelProvider
from src.services.inference.config import TextGenerationOptions
from src.services.inference.inference_service import get_inference_service
from src.storage.db import get_db
from src.storage.models import Chat, ChatMessage


class ChatService:
    """Service for handling chat operations"""

    def __init__(self, db: Session, inference_service: InferenceService):
        self.db = db
        self.inference_service = inference_service

    def create_chat(self, user_id: UUID, title: str) -> Chat:
        chat = Chat(user_id=user_id, title=title)
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_chat(self, chat_id: UUID) -> Optional[Chat]:
        return self.db.query(Chat).filter(Chat.id == chat_id).first()

    def get_user_chats(self, user_id: UUID) -> List[Chat]:
        return self.db.query(Chat).filter(Chat.user_id == user_id).all()

    def add_message(self, chat_id: UUID, role: str, content: str, provider: Optional[str] = None, model: Optional[str] = None) -> ChatMessage:
        message = ChatMessage(chat_id=chat_id, role=role, content=content, provider=provider, model=model)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def update_message(self, message_id: UUID, content: str) -> ChatMessage:
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise ValueError(f"Message with ID {message_id} not found")

        message.content = content
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_chat_messages(self, chat_id: UUID) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.created_at).all()

    def delete_chat(self, chat_id: UUID) -> bool:
        chat = self.get_chat(chat_id)
        if not chat:
            return False

        self.db.delete(chat)
        self.db.commit()
        return True

    async def generate_completion(
        self, provider: ModelProvider, model: str, messages: List[dict], options: Optional[TextGenerationOptions] = None
    ) -> str:
        # Format messages into a prompt
        prompt = self._format_messages_to_prompt(messages)

        # Get completion from inference service
        return await self.inference_service.generate_text(provider=provider, model=model, prompt=prompt, options=options)

    async def generate_completion_stream(
        self, provider: ModelProvider, model: str, messages: List[dict], options: Optional[TextGenerationOptions] = None
    ) -> AsyncGenerator[str, None]:
        # Format messages into a prompt
        prompt = self._format_messages_to_prompt(messages)

        # Get streaming completion from inference service
        async for chunk in self.inference_service.generate_text_stream(provider=provider, model=model, prompt=prompt, options=options):
            yield chunk

    def _format_messages_to_prompt(self, messages: List[dict]) -> str:
        """Format a list of messages into a prompt string"""
        formatted_messages = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "user":
                formatted_messages.append(f"User: {content}")
            elif role == "assistant":
                formatted_messages.append(f"Assistant: {content}")
            elif role == "system":
                formatted_messages.append(f"System: {content}")

        return "\n".join(formatted_messages)

    async def stream_response_format(self, text_stream) -> AsyncGenerator[str, None]:
        """Format the streaming response as SSE events"""
        async for chunk in text_stream:
            # Create SSE-formatted data
            data = json.dumps({"content": chunk, "type": "content"})
            yield f"data: {data}\n\n"

        # Send done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def _rewrite_chat_history(self, chat_id: UUID, messages: List[dict], provider: ModelProvider, model: str) -> None:
        """
        Rewrite the entire message history for a chat.
        This deletes all existing messages and adds the new ones.
        """
        # Delete all existing messages
        self.db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).delete()
        self.db.commit()

        # Add all new messages
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if content:  # Skip empty messages
                self.add_message(chat_id=chat_id, role=role, content=content, provider=provider.value, model=model)

    async def chat_completion_stream(
        self, user_id: UUID, messages: List[dict], provider: ModelProvider, model: str, options: Optional[TextGenerationOptions] = None, chat_id: Optional[UUID] = None
    ) -> AsyncGenerator[str, None]:
        if not chat_id:
            chat = self.create_chat(user_id=user_id, title="New Chat test")
            chat_id = chat.id
        else:
            chat = self.get_chat(chat_id)
            if not chat:
                raise ValueError(f"Chat with ID {chat_id} not found")

        # TODO: rewrite this logic
        await self._rewrite_chat_history(chat_id, messages, provider, model)

        assistant_message = self.add_message(chat_id=chat_id, role="assistant", content="", provider=provider.value, model=model)
        message_metadata = { 'id': str(assistant_message.id), 'role': assistant_message.role }
        yield f"data: {json.dumps({'type': 'message_start', 'message': message_metadata })}\n\n"

        assistant_content = ""
        # async for chunk in self.generate_completion_stream(provider=provider, model=model, messages=messages, options=options):
        async for chunk in self.fake_stream_response(messages[-1]["content"]):
            assistant_content += chunk
            content_metadata = { 'type': 'text', 'text': chunk }
            yield f"data: {json.dumps({'type': 'message_content', 'content': content_metadata })}\n\n"
        
        yield f"data: {json.dumps({'type': 'message_content_stop' })}\n\n"

        self.update_message(message_id=assistant_message.id, content=assistant_content)
        
        chat_metadata = {
            'type': 'chat_metadata',
            'chat': {
                'id': str(chat_id),
                'title': chat.title,
            }
        }
        yield f"data: {json.dumps(chat_metadata)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def fake_stream_response(self, message: str):
        # Simulate AI thinking and generating response
        response_parts = [
            "I'm thinking about",
            " your message regarding",
            f" '{message}'...",
            "\nHere's my response:",
            "\nThis is a mock streaming",
            " response that simulates",
            " real AI behavior",
            " with delays between chunks.",
        ]

        for part in response_parts:
            yield part
            await asyncio.sleep(0.5)  # Add delay between chunks

def get_chat_service(
    db: Session = Depends(get_db),
    inference_service = Depends(get_inference_service)
) -> ChatService:
    return ChatService(db=db, inference_service=inference_service)


chat_service = Annotated[ChatService, Depends(get_chat_service)]

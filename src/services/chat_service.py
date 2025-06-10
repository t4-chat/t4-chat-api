import asyncio
import json
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.services.inference import InferenceService, ModelProvider
from src.services.inference.config import TextGenerationOptions
from src.storage.models import Chat, ChatMessage


class ChatService:
    """Service for handling chat operations"""

    def __init__(self, db: Session, inference_service: InferenceService):
        self.db = db
        self.inference_service = inference_service

    def create_chat(self, user_id: UUID, title: str) -> Chat:
        """Create a new chat"""
        chat = Chat(user_id=user_id, title=title)
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_chat(self, chat_id: UUID) -> Optional[Chat]:
        """Get a chat by ID"""
        return self.db.query(Chat).filter(Chat.id == chat_id).first()

    def get_user_chats(self, user_id: UUID) -> List[Chat]:
        """Get all chats for a user"""
        return self.db.query(Chat).filter(Chat.user_id == user_id).all()

    def add_message(self, chat_id: UUID, role: str, content: str, provider: Optional[str] = None, model: Optional[str] = None) -> ChatMessage:
        """Add a message to a chat"""
        message = ChatMessage(chat_id=chat_id, role=role, content=content, provider=provider, model=model)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_chat_messages(self, chat_id: UUID) -> List[ChatMessage]:
        """Get all messages for a chat"""
        return self.db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.created_at).all()

    def delete_chat(self, chat_id: UUID) -> bool:
        """Delete a chat"""
        chat = self.get_chat(chat_id)
        if not chat:
            return False

        self.db.delete(chat)
        self.db.commit()
        return True

    async def generate_completion(
        self, provider: ModelProvider, model: str, messages: List[dict], options: Optional[TextGenerationOptions] = None
    ) -> str:
        """
        Generate a completion for a list of messages.
        This is for non-streaming responses.
        """
        # Format messages into a prompt
        prompt = self._format_messages_to_prompt(messages)

        # Get completion from inference service
        return await self.inference_service.generate_text(provider=provider, model=model, prompt=prompt, options=options)

    async def generate_completion_stream(
        self, provider: ModelProvider, model: str, messages: List[dict], options: Optional[TextGenerationOptions] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a completion for a list of messages in streaming mode.
        This returns chunks as they"re generated.
        """
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
        yield f"data: {json.dumps({"type": "done"})}\n\n"

    async def _rewrite_chat_history(self, chat_id: UUID, messages: List[dict]) -> None:
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
                self.add_message(chat_id=chat_id, role=role, content=content)

    async def chat_completion_stream(
        self, chat_id: UUID, messages: List[dict], provider: ModelProvider, model: str, options: Optional[TextGenerationOptions] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat message and generate a streaming response.
        This handles the database operations and calls the inference service.
        """
        chat = self.get_chat(chat_id)
        if not chat:
            raise ValueError(f"Chat with ID {chat_id} not found")

        # TODO: don't like this approach, let's rewrite this asap
        asyncio.create_task(self._rewrite_chat_history(chat_id, messages))

        # Generate and stream the response
        assistant_content = ""
        async for chunk in self.generate_completion_stream(provider=provider, model=model, messages=messages, options=options):
            assistant_content += chunk
            yield chunk

        # After streaming is complete, save the assistant's message
        self.add_message(chat_id=chat_id, role="assistant", content=assistant_content, provider=provider.value, model=model)

import asyncio
import json
from typing import Annotated, AsyncGenerator, List, Optional
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from src.config import settings
from src.services.errors.errors import NotFoundError
from src.services.inference import InferenceService
from src.services.inference.config import DefaultResponseGenerationOptions
from src.services.inference.inference_service import get_inference_service
from src.storage.db import get_db
from src.storage.models import Chat, ChatMessage
from src.storage.models.ai_provider import AiProvider
from src.storage.models.ai_provider_model import AiProviderModel


class ChatService:
    """Service for handling chat operations"""

    def __init__(self, db: Session, inference_service: InferenceService):
        self.db = db
        self.inference_service = inference_service

    def create_chat(self, user_id: UUID, title: Optional[str] = None) -> Chat:
        chat = Chat(user_id=user_id, title=title)
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_chat(self, chat_id: UUID) -> Optional[Chat]:
        return self.db.query(Chat).filter(Chat.id == chat_id).first()

    def get_user_chats(self, user_id: UUID) -> List[Chat]:
        return self.db.query(Chat).filter(Chat.user_id == user_id).all()

    def get_model(self, model_id: int) -> Optional[AiProviderModel]:
        return self.db.query(AiProviderModel).filter(AiProviderModel.id == model_id).first()

    def get_model_by_path(self, path: str) -> Optional[AiProviderModel]:
        provider_slug, model_name = path.split("/")
        return self.db.query(AiProviderModel).join(AiProviderModel.provider).filter(
            AiProvider.slug == provider_slug,
            AiProviderModel.name == model_name
        ).first()

    def get_provider(self, provider_id: int) -> Optional[AiProvider]:
        return self.db.query(AiProvider).filter(AiProvider.id == provider_id).first()

    def add_message(self, chat_id: UUID, role: str, content: str, model_id: int) -> ChatMessage:
        message = ChatMessage(chat_id=chat_id, role=role, content=content, model_id=model_id)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def update_message(self, message_id: UUID, content: str) -> ChatMessage:
        message = self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            raise NotFoundError(resource_name="Message", resource_id=message_id)

        message.content = content
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_chat_messages(self, chat_id: UUID) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.created_at).all()

    # TODO: maybe soft delete for now?
    def delete_chat(self, chat_id: UUID) -> bool:
        chat = self.get_chat(chat_id)
        if not chat:
            return False

        self.db.delete(chat)
        self.db.commit()
        return True
    
    def update_chat_title(self, chat_id: UUID, title: str):
        chat = self.get_chat(chat_id)
        if not chat:
            return None

        chat.title = title
        self.db.commit()
        self.db.refresh(chat)
        return chat
    
    def pin_chat(self, chat_id: UUID):
        chat = self.get_chat(chat_id)
        if not chat:
            return None

        chat.pinned = not chat.pinned
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def _prompt_or_default(self, prompt: Optional[str]) -> str:
        if prompt:
            return prompt
        else:
            return "You are a helpful assistant that can answer questions and help with tasks."  # TODO: not sure if we should handle this here, or on the database level

    async def _generate_completion(self, provider: AiProvider, model: AiProviderModel, messages: List[dict], options: Optional[DefaultResponseGenerationOptions] = None) -> str:
        return await self.inference_service.generate_response(provider=provider, model=model, messages=messages, options=options)

    async def _generate_completion_stream(
        self, provider: AiProvider, model: AiProviderModel, messages: List[dict], options: Optional[DefaultResponseGenerationOptions] = None
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.inference_service.generate_response_stream(provider=provider, model=model, messages=messages, options=options):
            yield chunk

    # TODO: remove?
    async def stream_response_format(self, text_stream) -> AsyncGenerator[str, None]:
        """Format the streaming response as SSE events"""
        async for chunk in text_stream:
            # Create SSE-formatted data
            data = json.dumps({"content": chunk, "type": "content"})
            yield f"data: {data}\n\n"

        # Send done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def _rewrite_chat_history(self, chat_id: UUID, messages: List[dict], model_id: int) -> None:
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
                self.add_message(chat_id=chat_id, role=role, content=content, model_id=model_id)

    async def _generate_chat_title(self, messages: List[dict]) -> None:
        model = self.get_model_by_path(settings.TITLE_GENERATION_MODEL)

        messages = [
            {
                "role": "system",
                "content": "Generate a concise and engaging title that summarizes the main topic or theme of the conversation between a user and an AI (or just the user question). The title should be clear, relevant, and attention-grabbing, ideally no longer than 8 words. Consider the key points, questions, or issues discussed in the conversation.",
            },
            *messages,
        ]

        # Generate title
        title = await self._generate_completion(provider=model.provider, model=model, messages=messages)
        return title.strip()
    
    def get_chat_title(self, chat_id: UUID) -> Optional[str]:
        chat = self.get_chat(chat_id)
        if not chat:
            return None
        return chat.title
    
    async def chat_completion_stream(
        self,
        user_id: UUID,
        messages: List[dict],
        provider_id: int,
        model_id: int,
        options: Optional[DefaultResponseGenerationOptions] = None,
        chat_id: Optional[UUID] = None,
    ) -> AsyncGenerator[str, None]:
        if not chat_id:
            title = await self._generate_chat_title(messages=messages)
            chat = self.create_chat(user_id=user_id, title=title)
            chat_id = chat.id
        else:
            chat = self.get_chat(chat_id)
            if not chat:
                raise NotFoundError(resource_name="Chat", resource_id=chat_id)

        # TODO: rewrite this logic (we need it to allow the user to edit the chat history, but might come up with a better solution)
        await self._rewrite_chat_history(chat_id, messages, model_id)

        assistant_message = self.add_message(chat_id=chat_id, role="assistant", content="", model_id=model_id)
        message_metadata = {"id": str(assistant_message.id), "role": assistant_message.role}

        # sending the first message, assistant message is already added to the db
        yield f"data: {json.dumps({'type': 'message_start', 'message': message_metadata })}\n\n"

        model = self.get_model(model_id)
        if not model:
            raise NotFoundError(resource_name="Model", resource_id=model_id)

        provider = self.get_provider(model.provider_id)
        if not provider:
            raise NotFoundError(resource_name="Provider", resource_id=model.provider_id)

        messages = [
            {"role": "system", "content": self._prompt_or_default(model.prompt)}
        ] + messages  # we don't want to expose the system prompt to the user, so we add it to the beginning of the message history

        assistant_content = ""
        async for chunk in self._generate_completion_stream(provider=provider, model=model, messages=messages, options=options):
            assistant_content += chunk
            content_metadata = {"type": "text", "text": chunk}
            yield f"data: {json.dumps({'type': 'message_content', 'content': content_metadata })}\n\n"
            # TODO: do we also want to save intermediate messages to the db?

        yield f"data: {json.dumps({'type': 'message_content_stop' })}\n\n"

        # update the assistant message with the final content
        self.update_message(message_id=assistant_message.id, content=assistant_content)

        chat_metadata = {
            "type": "chat_metadata",
            "chat": {
                "id": str(chat_id),
                "title": chat.title,
            },
        }
        yield f"data: {json.dumps(chat_metadata)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    #
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


def get_chat_service(db: Session = Depends(get_db), inference_service=Depends(get_inference_service)) -> ChatService:
    return ChatService(db=db, inference_service=inference_service)


chat_service = Annotated[ChatService, Depends(get_chat_service)]

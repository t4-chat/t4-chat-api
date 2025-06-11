import asyncio
import json
from typing import AsyncGenerator, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.services.context import Context
from src.services.errors import errors
from src.services.inference import InferenceService
from src.services.inference.config import DefaultResponseGenerationOptions
from src.services.inference.models.response_models import StreamGenerationResponse, TextGenerationResponse
from src.services.prompts_service import PromptsService
from src.storage.models import Chat, ChatMessage  # need to find a good way of differentiating between models and schemas
from src.api.schemas.chat import ChatMessage as ChatMessageSchema
from src.storage.models.ai_provider import AiProvider
from src.storage.models.ai_provider_model import AiProviderModel
from src.services.files_service import FilesService
from src.services import utils


class ChatService:
    def __init__(self, context: Context, db: AsyncSession, inference_service: InferenceService, prompts_service: PromptsService, files_service: FilesService):
        self.context = context
        self.db = db
        self.inference_service = inference_service
        self.prompts_service = prompts_service
        self.files_service = files_service

    async def create_chat(self, title: Optional[str] = None) -> Chat:
        chat = Chat(user_id=self.context.user_id, title=title)
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)
        return chat

    async def get_chat(self, chat_id: UUID) -> Optional[Chat]:
        results = await self.db.execute(select(Chat).options(selectinload(Chat.messages)).filter(Chat.id == chat_id, Chat.user_id == self.context.user_id))
        return results.scalars().first()

    async def get_user_chats(self) -> List[Chat]:
        results = await self.db.execute(select(Chat).filter(Chat.user_id == self.context.user_id))
        return results.scalars().all()

    async def get_model(self, model_id: int) -> Optional[AiProviderModel]:
        results = await self.db.execute(select(AiProviderModel).options(selectinload(AiProviderModel.provider)).filter(AiProviderModel.id == model_id))
        return results.scalar_one_or_none()

    async def get_model_by_path(self, path: str) -> Optional[AiProviderModel]:
        provider_slug, model_name = path.split("/")
        results = await self.db.execute(
            select(AiProviderModel)
            .join(AiProviderModel.provider)
            .options(selectinload(AiProviderModel.provider))
            .filter(AiProvider.slug == provider_slug, AiProviderModel.name == model_name)
        )
        return results.scalar_one_or_none()

    async def get_provider(self, provider_id: int) -> Optional[AiProvider]:
        results = await self.db.execute(select(AiProvider).filter(AiProvider.id == provider_id))
        return results.scalar_one_or_none()

    async def add_message(self, chat_id: UUID, role: str, model_id: int, content: str, attachments: Optional[List[UUID]] = None) -> ChatMessage:
        message = ChatMessage(chat_id=chat_id, role=role, content=content, model_id=model_id, attachments=attachments)
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def update_message(self, message_id: UUID, content: str) -> ChatMessage:
        results = await self.db.execute(select(ChatMessage).join(Chat, ChatMessage.chat_id == Chat.id).filter(ChatMessage.id == message_id, Chat.user_id == self.context.user_id))
        message = results.scalar_one_or_none()
        if not message:
            raise errors.NotFoundError(resource_name="Message", message=f"Message with id {message_id} not found")

        message.content = content
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def delete_chat(self, chat_id: UUID) -> bool:
        results = await self.db.execute(select(Chat).filter(Chat.id == chat_id, Chat.user_id == self.context.user_id))
        chat = results.scalar_one_or_none()
        if not chat:
            return False

        await self.db.delete(chat)
        await self.db.commit()
        return True

    async def update_chat_title(self, chat_id: UUID, title: str) -> Optional[Chat]:
        results = await self.db.execute(select(Chat).filter(Chat.id == chat_id, Chat.user_id == self.context.user_id))
        chat = results.scalar_one_or_none()
        if not chat:
            return None

        chat.title = title
        await self.db.commit()
        await self.db.refresh(chat)
        return chat

    async def pin_chat(self, chat_id: UUID) -> Optional[Chat]:
        results = await self.db.execute(select(Chat).filter(Chat.id == chat_id, Chat.user_id == self.context.user_id))
        chat = results.scalar_one_or_none()
        if not chat:
            return None

        chat.pinned = not chat.pinned
        await self.db.commit()
        await self.db.refresh(chat)
        return chat

    async def _generate_completion(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[dict],
        options: Optional[DefaultResponseGenerationOptions] = None,
        background_tasks: BackgroundTasks = None,
    ) -> TextGenerationResponse:
        return await self.inference_service.generate_response(provider=provider, model=model, messages=messages, options=options, background_tasks=background_tasks)

    async def _generate_completion_stream(
        self,
        provider: AiProvider,
        model: AiProviderModel,
        messages: List[ChatMessageSchema],
        options: Optional[DefaultResponseGenerationOptions] = None,
        background_tasks: BackgroundTasks = None,
    ) -> AsyncGenerator[StreamGenerationResponse, None]:
        async for chunk in self.inference_service.generate_response_stream(provider=provider, model=model, messages=messages, options=options, background_tasks=background_tasks):
            yield chunk

    async def stream_response_format(self, text_stream) -> AsyncGenerator[str, None]:
        """Format the streaming response as SSE events"""
        async for chunk in text_stream:
            # Create SSE-formatted data
            data = json.dumps({"content": chunk, "type": "content"})
            yield f"data: {data}\n\n"

        # Send done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def _rewrite_chat_history(self, chat_id: UUID, messages: List[ChatMessageSchema], model_id: int) -> None:
        """
        Rewrite the entire message history for a chat.
        This deletes all existing messages and adds the new ones.
        """
        # Delete all existing messages
        await self.db.execute(delete(ChatMessage).filter(ChatMessage.chat_id == chat_id, Chat.user_id == self.context.user_id))
        await self.db.commit()

        # Add all new messages
        for message in messages:
            await self.add_message(chat_id=chat_id, role=message.role, model_id=model_id, content=message.content, attachments=message.attachments)

    async def _generate_chat_title(self, messages: List[ChatMessageSchema], background_tasks: BackgroundTasks = None) -> str:
        model = await self.get_model_by_path(settings.TITLE_GENERATION_MODEL)
        if not model:
            raise errors.NotFoundError(resource_name="Model", message=f"Model with path {settings.TITLE_GENERATION_MODEL} not found")

        # Convert ChatMessage objects to dictionaries for the model
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]

        messages_for_title = [
            {
                "role": "system",
                "content": await self.prompts_service.get_prompt("title_generation"),
            },
            *messages_dict,
        ]

        title_response = await self._generate_completion(provider=model.provider, model=model, messages=messages_for_title, background_tasks=background_tasks)
        return title_response.text.strip()

    async def get_chat_title(self, chat_id: UUID) -> Optional[str]:
        results = await self.db.execute(select(Chat).filter(Chat.id == chat_id, Chat.user_id == self.context.user_id))
        chat = results.scalar_one_or_none()
        if not chat:
            return None
        return chat.title

    async def chat_completion_stream(
        self,
        messages: List[ChatMessageSchema],
        model_id: int,
        options: Optional[DefaultResponseGenerationOptions] = None,
        chat_id: Optional[UUID] = None,
        background_tasks: BackgroundTasks = None,
    ) -> AsyncGenerator[str, None]:
        if not chat_id:
            title = await self._generate_chat_title(messages=messages, background_tasks=background_tasks)
            chat = await self.create_chat(title=title)
            chat_id = chat.id
        else:
            results = await self.db.execute(select(Chat).filter(Chat.id == chat_id, Chat.user_id == self.context.user_id))
            chat = results.scalar_one_or_none()
            if not chat:
                raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {chat_id} not found")

        await self._rewrite_chat_history(chat_id, messages, model_id)

        assistant_message = await self.add_message(chat_id=chat_id, role="assistant", model_id=model_id, content="")
        message_metadata = {"id": str(assistant_message.id), "role": assistant_message.role}

        yield f"data: {json.dumps({'type': 'message_start', 'message': message_metadata })}\n\n"

        model = await self.get_model(model_id)
        if not model:
            raise errors.NotFoundError(resource_name="Model", message=f"Model with id {model_id} not found")

        provider = model.provider
        if not provider:
            raise errors.NotFoundError(resource_name="Provider", message=f"Provider with id {model.provider_id} not found")

        # Process attachments and add them to messages
        processed_messages = await self._prepare_messages(messages=messages)

        # Use processed messages for inference
        inference_messages = [{"role": "system", "content": await self.prompts_service.get_prompt(model.prompt_path)}] + processed_messages

        assistant_content = ""
        async for chunk in self._generate_completion_stream(provider=provider, model=model, messages=inference_messages, options=options, background_tasks=background_tasks):
            assistant_content += chunk.text
            content_metadata = {"type": "text", "text": chunk.text}
            yield f"data: {json.dumps({'type': 'message_content', 'content': content_metadata })}\n\n"

        yield f"data: {json.dumps({'type': 'message_content_stop' })}\n\n"

        await self.update_message(message_id=assistant_message.id, content=assistant_content)

        chat_metadata = {
            "type": "chat_metadata",
            "chat": {
                "id": str(chat_id),
                "title": chat.title,
            },
        }
        yield f"data: {json.dumps(chat_metadata)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def _prepare_messages(self, messages: List[ChatMessageSchema]) -> List[dict]:
        if not messages:
            return []

        model_messages = []
        for message in messages:
            content = [{"type": "text", "text": message.content}] if message.attachments else message.content

            if message.attachments:
                for attachment_id in message.attachments:
                    file_content = await self.files_service.get_file(attachment_id)
                    content.append(utils.prepare_file(file_content["metadata"]["content_type"], file_content["data"]))

            model_messages.append({"role": message.role, "content": content})

        return model_messages

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

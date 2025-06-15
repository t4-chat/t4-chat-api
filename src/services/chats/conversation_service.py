import asyncio
import json
from typing import AsyncGenerator, List, Optional

from fastapi import BackgroundTasks

from src.services.ai_providers.ai_model_service import AiModelService
from src.services.chats.chat_service import ChatService
from src.services.chats.dto import ChatMessageDTO
from src.services.chats.utils import stream_error_handler
from src.services.common import errors
from src.services.common.context import Context
from src.services.files import utils
from src.services.files.files_service import FilesService
from src.services.inference import InferenceService
from src.services.inference.dto import DefaultResponseGenerationOptionsDTO, StreamGenerationDTO, TextGenerationDTO
from src.services.prompts.prompts_service import PromptsService

from src.services.ai_providers.dto import AiProviderDTO, AiProviderModelDTO

from src.config import settings
from src.logging.logging_config import get_logger

logger = get_logger(__name__)


class ConversationService:
    def __init__(
        self,
        context: Context,
        chat_service: ChatService,
        inference_service: InferenceService,
        prompts_service: PromptsService,
        files_service: FilesService,
        ai_model_service: AiModelService,
    ):
        self.context = context
        self.chat_service = chat_service
        self.inference_service = inference_service
        self.prompts_service = prompts_service
        self.files_service = files_service
        self.ai_model_service = ai_model_service

    async def _generate_completion(
        self,
        provider: AiProviderDTO,
        model: AiProviderModelDTO,
        messages: List[dict],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        background_tasks: BackgroundTasks = None,
    ) -> TextGenerationDTO:
        return await self.inference_service.generate_response(
            provider=provider,
            model=model,
            messages=messages,
            options=options,
            background_tasks=background_tasks,
        )

    async def _generate_completion_stream(
        self,
        provider: AiProviderDTO,
        model: AiProviderModelDTO,
        messages: List[ChatMessageDTO],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        background_tasks: BackgroundTasks = None,
    ) -> AsyncGenerator[StreamGenerationDTO, None]:
        async for chunk in self.inference_service.generate_response_stream(
            provider=provider,
            model=model,
            messages=messages,
            options=options,
            background_tasks=background_tasks,
        ):
            yield chunk

    async def _stream_response_format(self, text_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        async for chunk in text_stream:
            # Create SSE-formatted data
            data = json.dumps({"content": chunk, "type": "content"})
            yield f"data: {data}\n\n"

        # Send done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    async def _rewrite_chat_history(self, message: ChatMessageDTO) -> None:
        """
        Rewrite the entire message history for a chat.
        This deletes all existing messages and adds the new ones.
        """

        if message.id:
            await self.chat_service.delete_all_later_messages(message)

        message.role = "user"
        await self.chat_service.add_message(message)

    async def _generate_chat_title(self, message: ChatMessageDTO, background_tasks: BackgroundTasks = None) -> str:
        model = await self.ai_model_service.get_model_by_path(settings.TITLE_GENERATION_MODEL)
        if not model:
            raise errors.NotFoundError(
                resource_name="Model",
                message=f"Model with path {settings.TITLE_GENERATION_MODEL} not found",
            )

        # Convert ChatMessage objects to dictionaries for the model
        messages_dict = [{"role": message.role, "content": message.content}]

        messages_for_title = [
            {
                "role": "system",
                "content": await self.prompts_service.get_prompt("title_generation"),
            },
            *messages_dict,
        ]

        if settings.MOCK_AI_RESPONSE:
            return "New Mock Chat Title"

        title_response = await self._generate_completion(
            provider=model.provider,
            model=model,
            messages=messages_for_title,
            background_tasks=background_tasks,
        )

        return title_response.text.strip()

    async def _prepare_messages(self, messages: List[ChatMessageDTO], model: AiProviderModelDTO) -> List[dict]:
        """
        Prepare messages for inference, including processing attachments.
        """
        if not messages:
            return []

        # Add system prompt
        model_messages = [
            {
                "role": "system",
                "content": await self.prompts_service.get_prompt(model.prompt_path),
                "cache_control": {"type": "ephemeral"},
            }
        ]

        # Process each message
        for message in messages:
            content = [{"type": "text", "text": message.content}] if message.attachments else message.content

            # Process attachments
            if message.attachments:
                for attachment_id in message.attachments:
                    file_content = await self.files_service.get_file(attachment_id)
                    content.append(utils.prepare_file(file_content.content_type, file_content.data))

            model_messages.append({"role": message.role, "content": content})

        return model_messages

    async def _fake_stream_response(self, *args, **kwargs):
        """
        Generate a fake streaming response for testing purposes.
        """
        response_parts = [
            "I'm thinking about",
            " your message regarding",
            f" '{kwargs['messages'][-1]}'...",
            "\nHere's my response:",
            "\nThis is a mock streaming",
            " response that simulates",
            " real AI behavior",
            " with delays between chunks.",
        ]

        for part in response_parts:
            yield StreamGenerationDTO(text=part)
            await asyncio.sleep(0.5)  # Add delay between chunks

    @stream_error_handler
    async def chat_completion_stream(
        self,
        model_id: int,
        message: ChatMessageDTO,
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        background_tasks: BackgroundTasks = None,
    ) -> AsyncGenerator[str, None]:
        if not message.chat_id:
            title = await self._generate_chat_title(message=message, background_tasks=background_tasks)
            chat = await self.chat_service.create_chat(title=title)
            chat_id = chat.id
            message.chat_id = chat_id
        else:
            chat = await self.chat_service.get_chat(chat_id=message.chat_id)
            if not chat:
                raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {message.chat_id} not found")
            chat_id = chat.id

        chat_metadata = {
            "type": "chat_metadata",
            "chat": {
                "id": str(chat_id),
                "title": chat.title,
            },
        }
        yield f"data: {json.dumps(chat_metadata)}\n\n"

        await self._rewrite_chat_history(message=message)

        prev_messages = await self.chat_service.get_messages(chat_id)

        assistant_message = await self.chat_service.add_message(
            ChatMessageDTO(
                chat_id=chat_id,
                role="assistant",
                model_id=model_id,
            )
        )

        message_metadata = {
            "id": str(assistant_message.id),
            "role": assistant_message.role,
        }
        yield f"data: {json.dumps({'type': 'message_start', 'message': message_metadata })}\n\n"

        model = await self.ai_model_service.get_model(model_id)
        if not model:
            raise errors.NotFoundError(resource_name="Model", message=f"Model with id {model_id} not found")

        provider = model.provider
        if not provider:
            raise errors.NotFoundError(
                resource_name="Provider",
                message=f"Provider with id {model.provider_id} not found",
            )

        inference_messages = await self._prepare_messages(messages=prev_messages, model=model)

        assistant_content = ""

        generate_stream_func = self._generate_completion_stream if not settings.MOCK_AI_RESPONSE else self._fake_stream_response

        async for chunk in generate_stream_func(
            provider=provider,
            model=model,
            messages=inference_messages,
            options=options,
            background_tasks=background_tasks,
        ):
            assistant_content += chunk.text
            content_metadata = {"type": "text", "text": chunk.text}
            yield f"data: {json.dumps({'type': 'message_content', 'content': content_metadata })}\n\n"

        yield f"data: {json.dumps({'type': 'message_content_stop' })}\n\n"

        await self.chat_service.update_message(message_id=assistant_message.id, content=assistant_content)

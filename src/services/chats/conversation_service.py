import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from fastapi import BackgroundTasks

from src.services.ai_providers.ai_model_service import AiModelService
from src.services.chats.chat_service import ChatService
from src.services.chats.dto import ChatMessageDTO, CompletionOptionsRequestDTO
from src.services.chats.utils import stream_error_handler
from src.services.common import errors
from src.services.common.context import Context
from src.services.files import utils
from src.services.files.files_service import FilesService
from src.services.inference import InferenceService
from src.services.inference.dto import DefaultResponseGenerationOptionsDTO, StreamGenerationDTO, TextGenerationDTO
from src.services.limits.limits_service import LimitsService
from src.services.prompts.prompts_service import PromptsService

from src.services.ai_providers.dto import AiProviderModelDTO

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
        limits_service: LimitsService,
    ):
        self.context = context
        self.chat_service = chat_service
        self.inference_service = inference_service
        self.prompts_service = prompts_service
        self.files_service = files_service
        self.ai_model_service = ai_model_service
        self.limits_service = limits_service

    async def _generate_completion(
        self,
        model: AiProviderModelDTO,
        messages: List[dict],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        background_tasks: BackgroundTasks = None,
    ) -> TextGenerationDTO:
        return await self.inference_service.generate_response(
            model=model,
            messages=messages,
            options=options,
            background_tasks=background_tasks,
        )

    async def _generate_completion_stream(
        self,
        model: AiProviderModelDTO,
        messages: List[ChatMessageDTO],
        options: Optional[DefaultResponseGenerationOptionsDTO] = None,
        background_tasks: BackgroundTasks = None,
    ) -> AsyncGenerator[StreamGenerationDTO, None]:
        async for chunk in self.inference_service.generate_response_stream(
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

    async def _rewrite_chat_history(self, message: ChatMessageDTO) -> ChatMessageDTO:
        """
        Rewrite the entire message history for a chat.
        This deletes all existing messages and adds the new ones.

        Returns the new message.
        """

        if message.id:
            await self.chat_service.delete_conversation_turn_from_point(message)

        # For user messages, we need to determine the previous message and sequence
        last_assistant = None
        seq_num = 1  # Default for first message

        # Get the last assistant message to link to
        messages = await self.chat_service.get_messages(message.chat_id)
        assistant_messages = [msg for msg in messages if msg.role == "assistant"]
        if assistant_messages:
            last_assistant = assistant_messages[-1]  # Get the last one
            seq_num = last_assistant.seq_num + 1
        else:
            # No assistant messages, get max seq_num + appropriate increment
            max_seq = await self.chat_service.get_max_sequence_number(message.chat_id)
            if max_seq == 0:
                seq_num = 1  # Very first message
            else:
                seq_num = max_seq + 2  # User messages increment by 2 when no assistant responses

        message.role = "user"
        return await self.chat_service.add_message(message, seq_num=seq_num)

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
            model=model,
            messages=messages_for_title,
            background_tasks=background_tasks,
        )

        return title_response.text.strip()

    async def _prepare_messages(self, messages: List[ChatMessageDTO], model: AiProviderModelDTO, options: Optional[CompletionOptionsRequestDTO] = None) -> List[dict]:
        """
        Prepare messages for inference, including processing attachments.
        """
        if not messages:
            return []
        
        params = {}
        if options:
            params["web_search"] = options.tools and "web_search" in options.tools

        # Add system prompt
        model_messages = [
            {
                "role": "system",
                "content": await self.prompts_service.get_prompt(model.prompt_path, params),
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
        reasoning_parts = [
            "Analyzing the context of your message...",
            "Considering relevant information...", 
            "Formulating a comprehensive response..."
        ]

        for part in reasoning_parts:
            yield StreamGenerationDTO(text=None, reasoning=part)
            await asyncio.sleep(0.5)

        response_parts = [
            "Based on my analysis,",
            " I understand you're asking about",
            f" '{kwargs['messages'][-1]}'.",
            "\nHere's my detailed response:",
            "\nThis is a mock streaming",
            " response that simulates",
            " real AI behavior",
            " with carefully considered output."
        ]

        for part in response_parts:
            yield StreamGenerationDTO(text=part)
            await asyncio.sleep(0.5)

    async def _setup_multi_model_chat(
        self,
        model_ids: List[UUID],
        message: ChatMessageDTO,
        background_tasks: BackgroundTasks = None,
        shared_conversation_id: Optional[UUID] = None,
    ):
        if not message.chat_id:
            if shared_conversation_id:
                chat = await self.chat_service.create_chat_from_shared_conversation(shared_conversation_id=shared_conversation_id)
            else:
                title = await self._generate_chat_title(message=message, background_tasks=background_tasks)
                chat = await self.chat_service.create_chat(title=title)
            
            chat_id = chat.id
            message.chat_id = chat_id
        else:
            chat = await self.chat_service.get_chat(chat_id=message.chat_id)
            if not chat:
                raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {message.chat_id} not found")
            chat_id = chat.id

        new_message = await self._rewrite_chat_history(message=message)
        msgs = await self.chat_service.get_messages(chat_id)
        prev_messages = [msg for msg in msgs if msg.selected or msg.selected is None]  # only get selected messages

        assistant_messages = []
        models = []

        for idx, model_id in enumerate(model_ids):
            model = await self.ai_model_service.get_model(model_id)
            if not model:
                raise errors.NotFoundError(resource_name="Model", message=f"Model with id {model_id} not found")
            models.append(model)

            assistant_message = await self.chat_service.add_message(
                ChatMessageDTO(
                    chat_id=chat_id,
                    role="assistant",
                    model_id=model_id,
                    selected=idx == 0,  # First model is selected by default
                ),
                seq_num=new_message.seq_num + 1,
                previous_message_id=new_message.id,
            )
            assistant_messages.append(assistant_message)

        return chat, new_message, prev_messages, models, assistant_messages

    async def _ensure_limits(self, model: AiProviderModelDTO, messages: List[Dict[str, Any]]):
        # if model has api key, we don't need to check limits
        if model.has_api_key:
            return
        if await self.limits_service.check_utilization(model.id, messages):
            raise errors.LimitsExceededError(f"Model {model.id} has exceeded its limit")

    async def _generate_model_response_stream(self, model, assistant_message, prev_messages, chunk_queue, background_tasks=None):
        """Generate response for a single model and put chunks in queue for real-time streaming"""
        inference_messages = await self._prepare_messages(messages=prev_messages, model=model)
        assistant_content = ""

        generate_stream_func = self._generate_completion_stream if not settings.MOCK_AI_RESPONSE else self._fake_stream_response

        try:
            async for chunk in generate_stream_func(
                model=model,
                messages=inference_messages,
                background_tasks=background_tasks,
            ):
                if chunk.reasoning:
                    chunk_data = {"type": "reasoning_content", "model_id": str(model.id), "message_id": str(assistant_message.id), "content": {"type": "text", "text": chunk.reasoning}}
                    await chunk_queue.put(chunk_data)
                # TODO: check if this is needed
                # if chunk.thinking and len(chunk.thinking) > 0:
                #     for thinking_chunk in chunk.thinking:
                #         chunk_data = {"type": "thinking_content", "model_id": str(model.id), "message_id": str(assistant_message.id), "content": {"type": "text", "text": thinking_chunk.thinking}}
                #         await chunk_queue.put(chunk_data)
                if chunk.text:
                    assistant_content += chunk.text
                    chunk_data = {"type": "message_content", "model_id": str(model.id), "message_id": str(assistant_message.id), "content": {"type": "text", "text": chunk.text}}
                    await chunk_queue.put(chunk_data)

            # Send stop chunk with final content
            stop_chunk = {"type": "message_content_stop", "model_id": str(model.id), "message_id": str(assistant_message.id), "final_content": assistant_content}
            await chunk_queue.put(stop_chunk)

        except Exception as e:
            logger.error(f"Error in model {model.id} generation: {e}")
            error_code = e.status_code if hasattr(e, "status_code") else 500
            error_chunk = {"type": "error", "model_id": str(model.id), "message_id": str(assistant_message.id), "error": str(e), "code": error_code}
            await chunk_queue.put(error_chunk)

    @stream_error_handler
    async def chat_completion_stream(
        self,
        model_ids: List[UUID],
        message: ChatMessageDTO,
        shared_conversation_id: Optional[UUID] = None,
        options: Optional[CompletionOptionsRequestDTO] = None,
        background_tasks: BackgroundTasks = None,
    ) -> AsyncGenerator[str, None]:
        # TODO: we are aware that there could be a race condition here
        chat, new_message, prev_messages, models, assistant_messages = await self._setup_multi_model_chat(model_ids, message, background_tasks, shared_conversation_id)

        chat_metadata = {
            "type": "chat_metadata",
            "chat": {"id": str(chat.id), "title": chat.title},
        }
        yield f"data: {json.dumps(chat_metadata)}\n\n"

        # Send message start metadata for all models
        for model, assistant_message in zip(models, assistant_messages):
            message_metadata = {
                "reply_to": str(new_message.id),
                "id": str(assistant_message.id),
                "role": assistant_message.role,
                "model_id": str(model.id),
                "model_name": model.name,
            }
            yield f"data: {json.dumps({'type': 'message_start', 'message': message_metadata})}\n\n"

        # TODO: move this to tasks to remove duplication of _prepare_messages. 
        # Check limits for all models first - this will raise LimitsExceededError immediately if needed
        for model in models:
            inference_messages = await self._prepare_messages(messages=prev_messages, model=model, options=options)
            await self._ensure_limits(model, inference_messages)

        chunk_queue = asyncio.Queue()

        tasks = [
            asyncio.create_task(self._generate_model_response_stream(model, assistant_message, prev_messages, chunk_queue, background_tasks))
            for model, assistant_message in zip(models, assistant_messages)
        ]

        # Track final contents for database updates
        final_contents = {}
        completed_models = 0
        total_models = len(models)

        while completed_models < total_models:
            chunk = await chunk_queue.get()

            if chunk.get("type") == "message_content_stop" and "final_content" in chunk:
                # Store final content for later database update
                final_contents[chunk["message_id"]] = chunk["final_content"]
                completed_models += 1
                # Remove final_content from the chunk before sending to client
                chunk_to_send = {k: v for k, v in chunk.items() if k != "final_content"}
                yield f"data: {json.dumps(chunk_to_send)}\n\n"
            elif chunk.get("type") == "error":
                completed_models += 1
                yield f"data: {json.dumps(chunk)}\n\n"
            else:
                yield f"data: {json.dumps(chunk)}\n\n"

        await asyncio.gather(*tasks, return_exceptions=True)

        # Now update all messages sequentially to avoid session conflicts
        for message_id, content in final_contents.items():
            await self.chat_service.update_message(message_id=UUID(message_id), content=content)

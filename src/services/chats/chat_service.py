from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_

from src.services.chats.dto import ChatDTO, ChatMessageDTO
from src.services.common import errors
from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto

from src.storage.base_repo import BaseRepository
from src.storage.models import Chat, ChatMessage

from src.logging.logging_config import get_logger

logger = get_logger(__name__)


class ChatService:
    def __init__(
        self,
        context: Context,
        chat_repo: BaseRepository[Chat],
        chat_message_repo: BaseRepository[ChatMessage],
    ):
        self.context = context
        self.chat_repo = chat_repo
        self.chat_message_repo = chat_message_repo

    @convert_to_dto
    async def create_chat(self, title: Optional[str] = None) -> ChatDTO:
        if not title:
            title = "New Chat"

        chat = Chat(user_id=self.context.user_id, title=title)
        chat = await self.chat_repo.add(chat)
        return chat

    async def get_chat(self, chat_id: UUID) -> Optional[ChatDTO]:
        return await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id),
            includes=[Chat.messages],
        )

    @convert_to_dto
    async def get_user_chats(self) -> List[ChatDTO]:
        return await self.chat_repo.get_all(filter=Chat.user_id == self.context.user_id)

    @convert_to_dto
    async def add_message(
        self,
        chat_id: UUID,
        role: str,
        model_id: int,
        content: str,
        attachments: Optional[List[UUID]] = None,
    ) -> ChatMessageDTO:
        # Verify the chat exists and belongs to the user
        chat = await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id)
        )
        if not chat:
            raise errors.NotFoundError(
                resource_name="Chat", message=f"Chat with id {chat_id} not found"
            )

        message = ChatMessage(
            chat_id=chat_id,
            role=role,
            content=content,
            model_id=model_id,
            attachments=attachments,
        )
        message = await self.chat_message_repo.add(message)
        return message

    @convert_to_dto
    async def update_message(self, message_id: UUID, content: str) -> ChatMessageDTO:
        message = await self.chat_message_repo.get(
            joins=[(Chat, Chat.id == ChatMessage.chat_id)],
            filter=and_(
                ChatMessage.id == message_id, Chat.user_id == self.context.user_id
            ),
        )

        if not message:
            raise errors.NotFoundError(
                resource_name="Message",
                message=f"Message with id {message_id} not found",
            )

        message.content = content
        message = await self.chat_message_repo.update(message)
        return message

    async def delete_chat(self, chat_id: UUID) -> bool:
        chat = await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id)
        )

        if not chat:
            return False

        await self.chat_repo.delete(chat)
        return True

    @convert_to_dto
    async def update_chat_title(self, chat_id: UUID, title: str) -> Optional[ChatDTO]:
        chat = await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id)
        )

        if not chat:
            raise errors.NotFoundError(
                resource_name="Chat", message=f"Chat with id {chat_id} not found"
            )

        chat.title = title
        chat = await self.chat_repo.update(chat)
        return chat

    @convert_to_dto
    async def pin_chat(self, chat_id: UUID) -> Optional[ChatDTO]:
        chat = await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id)
        )

        if not chat:
            raise errors.NotFoundError(
                resource_name="Chat", message=f"Chat with id {chat_id} not found"
            )

        chat.pinned = not chat.pinned
        chat = await self.chat_repo.update(chat)
        return chat

    async def get_chat_title(self, chat_id: UUID) -> Optional[str]:
        chat = await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id)
        )

        if not chat:
            raise errors.NotFoundError(
                resource_name="Chat", message=f"Chat with id {chat_id} not found"
            )

        return chat.title

    async def delete_all_messages(self, chat_id: UUID) -> bool:
        chat = await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id)
        )
        if not chat:
            return False

        await self.chat_message_repo.delete_by_filter(
            filter=ChatMessage.chat_id == chat_id
        )
        return True

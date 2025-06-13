import json
import traceback
from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.services.context import Context
from src.services.errors import errors
from src.storage.models import Chat, ChatMessage
from src.logging.logging_config import get_logger

logger = get_logger(__name__)


class ChatService:
    def __init__(
        self,
        context: Context,
        db: AsyncSession,
    ):
        self.context = context
        self.db = db

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

    async def add_message(self, chat_id: UUID, role: str, model_id: int, content: str, attachments: Optional[List[UUID]] = None) -> ChatMessage:
        # Verify the chat exists and belongs to the user
        chat = await self.get_chat(chat_id)
        if not chat:
            raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {chat_id} not found")

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

    async def get_chat_title(self, chat_id: UUID) -> Optional[str]:
        results = await self.db.execute(select(Chat).filter(Chat.id == chat_id, Chat.user_id == self.context.user_id))
        chat = results.scalar_one_or_none()

        if not chat:
            return None

        return chat.title

    async def delete_all_messages(self, chat_id: UUID) -> bool:
        # Verify the chat exists and belongs to the user
        chat = await self.get_chat(chat_id)
        if not chat:
            return False

        await self.db.execute(delete(ChatMessage).filter(ChatMessage.chat_id == chat_id))
        await self.db.commit()
        return True

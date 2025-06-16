from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select

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

    @convert_to_dto
    async def get_chat(self, chat_id: UUID) -> Optional[ChatDTO]:
        return await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id),
            includes=[Chat.messages],
        )

    @convert_to_dto
    async def get_messages(self, chat_id: UUID) -> List[ChatMessageDTO]:
        return await self.chat_message_repo.select(
            joins=[(Chat, Chat.id == ChatMessage.chat_id)],
            filter=and_(ChatMessage.chat_id == chat_id, Chat.user_id == self.context.user_id, ChatMessage.content.isnot(None)),
            order_by=[ChatMessage.seq_num.asc()],
        )

    @convert_to_dto
    async def get_last_message(self, chat_id: UUID) -> Optional[ChatMessageDTO]:
        return await self.chat_message_repo.get(
            joins=[(Chat, Chat.id == ChatMessage.chat_id)],
            filter=and_(ChatMessage.chat_id == chat_id, Chat.user_id == self.context.user_id),
            order_by=[ChatMessage.seq_num.desc()],
        )

    @convert_to_dto
    async def get_user_chats(self) -> List[ChatDTO]:
        return await self.chat_repo.select(filter=Chat.user_id == self.context.user_id)

    @convert_to_dto
    async def add_message(
        self,
        message: ChatMessageDTO,
        seq_num: int,
        previous_message_id: Optional[UUID] = None,
    ) -> ChatMessageDTO:
        # Verify the chat exists and belongs to the user
        chat = await self.chat_repo.get(filter=and_(Chat.id == message.chat_id, Chat.user_id == self.context.user_id))
        if not chat:
            raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {message.chat_id} not found")

        chat_message = ChatMessage(**message.model_dump(exclude={"seq_num", "previous_message_id"}))
        chat_message.seq_num = seq_num
        chat_message.previous_message_id = previous_message_id

        return await self.chat_message_repo.add(chat_message)

    @convert_to_dto
    async def update_message(self, message_id: UUID, content: str) -> ChatMessageDTO:
        message = await self.chat_message_repo.get(
            joins=[(Chat, Chat.id == ChatMessage.chat_id)],
            filter=and_(ChatMessage.id == message_id, Chat.user_id == self.context.user_id),
        )

        if not message:
            raise errors.NotFoundError(
                resource_name="Message",
                message=f"Message with id {message_id} not found",
            )

        message.content = content
        return await self.chat_message_repo.update(message)

    async def delete_chats(self, chat_ids: List[UUID]) -> None:
        await self.chat_repo.delete_by_filter(filter=and_(Chat.id.in_(chat_ids), Chat.user_id == self.context.user_id))

    @convert_to_dto
    async def update_chat_title(self, chat_id: UUID, title: str) -> Optional[ChatDTO]:
        chat = await self.chat_repo.get(filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id))

        if not chat:
            raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {chat_id} not found")

        chat.title = title
        chat = await self.chat_repo.update(chat)
        return chat

    @convert_to_dto
    async def pin_chat(self, chat_id: UUID) -> Optional[ChatDTO]:
        chat = await self.chat_repo.get(filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id))

        if not chat:
            raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {chat_id} not found")

        chat.pinned = not chat.pinned
        chat = await self.chat_repo.update(chat)
        return chat

    async def get_chat_title(self, chat_id: UUID) -> Optional[str]:
        chat = await self.chat_repo.get(filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id))

        if not chat:
            raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {chat_id} not found")

        return chat.title

    async def delete_conversation_turn_from_point(self, message: ChatMessageDTO) -> bool:
        if not message.id:
            return False

        chat = await self.chat_repo.get(filter=and_(Chat.id == message.chat_id, Chat.user_id == self.context.user_id))
        if not chat:
            return False

        # Get the message to delete from
        db_message = await self.chat_message_repo.get(
            joins=[(Chat, Chat.id == ChatMessage.chat_id)],
            filter=and_(ChatMessage.id == message.id, Chat.user_id == self.context.user_id),
            includes=[ChatMessage.previous_message],
        )

        if not db_message:
            return False

        if db_message.role == "user":
            # For user messages, delete this message and everything after it (>=)
            await self.chat_message_repo.delete_by_filter(filter=and_(ChatMessage.chat_id == message.chat_id, ChatMessage.seq_num >= db_message.seq_num))
        else:
            user_message = db_message.previous_message

            # Delete everything after the user message, but not the user message itself (>)
            await self.chat_message_repo.delete_by_filter(filter=and_(ChatMessage.chat_id == message.chat_id, ChatMessage.seq_num > user_message.seq_num))

        return True

    @convert_to_dto
    async def select_message(self, chat_id: UUID, message_id: UUID) -> ChatMessageDTO:
        # TODO: we are aware that if we change selection - then previous_message_id for the next user message will be wrong
        message = await self.chat_message_repo.get(
            joins=[(Chat, Chat.id == ChatMessage.chat_id)],
            filter=and_(ChatMessage.id == message_id, ChatMessage.chat_id == chat_id, Chat.user_id == self.context.user_id),
        )

        if not message:
            raise errors.NotFoundError(
                resource_name="Message",
                message=f"Message with id {message_id} not found in chat {chat_id}",
            )

        # Unselect all other messages with the same previous_message_id (same generation batch)
        if message.previous_message_id:
            await self.chat_message_repo.bulk_update(
                filter=and_(ChatMessage.previous_message_id == message.previous_message_id, ChatMessage.id != message_id), values={"selected": False}
            )

        # Select the target message
        message.selected = True
        return await self.chat_message_repo.update(message)

    async def get_max_sequence_number(self, chat_id: UUID) -> int:
        stmt = select(func.coalesce(func.max(ChatMessage.seq_num), 0)).where(ChatMessage.chat_id == chat_id)
        result = await self.chat_message_repo.session.execute(stmt)
        return result.scalar()

from typing import List, Optional
from uuid import UUID
import uuid

from sqlalchemy import and_, func, select

from src.services.chats.dto import ChatDTO, ChatMessageDTO, SharedConversationListItemDTO
from src.services.common import errors
from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto

from src.storage.base_repo import BaseRepository
from src.storage.models import Chat, ChatMessage, SharedConversation

from src.logging.logging_config import get_logger

logger = get_logger(__name__)


class ChatService:
    def __init__(
        self,
        context: Context,
        chat_repo: BaseRepository[Chat],
        chat_message_repo: BaseRepository[ChatMessage],
        shared_conversation_repo: BaseRepository[SharedConversation],
    ):
        self.context = context
        self.chat_repo = chat_repo
        self.chat_message_repo = chat_message_repo
        self.shared_conversation_repo = shared_conversation_repo

    @convert_to_dto
    async def create_chat(self, title: Optional[str] = None) -> ChatDTO:
        if not title:
            title = "New Chat"

        chat = Chat(user_id=self.context.user_id, title=title)
        chat = await self.chat_repo.add(chat)
        return chat
    
    @convert_to_dto
    async def create_chat_from_shared_conversation(self, shared_conversation_id: UUID) -> ChatDTO:
        existing_chat = await self.chat_repo.get(
            joins=[(SharedConversation, SharedConversation.chat_id == Chat.id)],
            filter=SharedConversation.id == shared_conversation_id,
            includes=[Chat.messages]
        )

        if not existing_chat:
            raise errors.NotFoundError(resource_name="Chat", message=f"Chat with shared conversation id {shared_conversation_id} not found")

        new_chat = Chat(
            user_id=self.context.user_id,
            title=existing_chat.title,
            messages=self._copy_messages(existing_chat.messages)
        )

        new_chat = await self.chat_repo.add(new_chat)
        return new_chat

    @convert_to_dto
    async def get_chat(self, chat_id: UUID) -> Optional[ChatDTO]:
        chat = await self.chat_repo.get(
            filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id),
            includes=[Chat.messages, Chat.shared_conversation],
        )
        return chat

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
        return await self.chat_repo.select(filter=Chat.user_id == self.context.user_id, includes=[Chat.shared_conversation])

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
    
    async def share_chat(self, chat_id: UUID) -> UUID:
        chat = await self.chat_repo.get(filter=and_(Chat.id == chat_id, Chat.user_id == self.context.user_id), includes=[Chat.shared_conversation])
        if not chat:
            raise errors.NotFoundError(resource_name="Chat", message=f"Chat with id {chat_id} not found")
        
        if chat.shared_conversation:
            return chat.shared_conversation.id
        
        shared_conversation = SharedConversation(chat_id=chat_id)
        shared_conversation = await self.shared_conversation_repo.add(shared_conversation)
        return shared_conversation.id
    

    async def get_shared_chats(self) -> List[SharedConversationListItemDTO]:
        return await self.shared_conversation_repo.select(
            joins=[(Chat, Chat.id == SharedConversation.chat_id)],
            filter=Chat.user_id == self.context.user_id,
            includes=[SharedConversation.chat]
        )


    async def get_shared_chat(self, shared_conversation_id: UUID) -> Optional[ChatDTO]:
        return await self.chat_repo.get(
            joins=[(SharedConversation, Chat.id == SharedConversation.chat_id)],
            filter=SharedConversation.id == shared_conversation_id,
            includes=[Chat.messages, Chat.shared_conversation]
        )
    
    
    async def unshare_chats(self, shared_conversation_ids: List[UUID]) -> None:
        shared_conversations = await self.shared_conversation_repo.select(
            joins=[(Chat, Chat.id == SharedConversation.chat_id)],
            filter=and_(SharedConversation.id.in_(shared_conversation_ids), Chat.user_id == self.context.user_id)
        )
        ids_to_delete = [sc.id for sc in shared_conversations]
        await self.shared_conversation_repo.delete_by_filter(filter=SharedConversation.id.in_(ids_to_delete))   
    

    def _copy_messages(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        sorted_messages = sorted(messages, key=lambda msg: msg.seq_num)
        new_messages = []
        previous_message_id = None
        
        for msg in sorted_messages:
            new_message = ChatMessage(
                id=uuid.uuid4(),
                role=msg.role,
                content=msg.content,
                selected=msg.selected,
                model_id=msg.model_id,
                attachments=msg.attachments,
                seq_num=msg.seq_num
            )
            
            if msg.role == "user":
                previous_message_id = new_message.id
            elif msg.role == "assistant":
                new_message.previous_message_id = previous_message_id
            
            new_messages.append(new_message)
        
        return new_messages
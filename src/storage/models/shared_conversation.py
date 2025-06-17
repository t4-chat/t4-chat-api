from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class SharedConversation(BaseModel):
    __tablename__ = "shared_conversations"
    __table_args__ = {"schema": "agg_ai"}

    chat_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.chats.id", ondelete="CASCADE"), nullable=False)

    chat = relationship("Chat", back_populates="shared_conversation", lazy="noload")

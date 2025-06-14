import uuid

from sqlalchemy import ARRAY, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class Chat(BaseModel):
    """Chat conversation model"""
    __tablename__ = "chats"
    __table_args__ = {"schema": "agg_ai"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)
    pinned = Column(Boolean, nullable=False, default=False)
    
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan", lazy="noload")
    user = relationship("User", back_populates="chats", lazy="noload")


class ChatMessage(BaseModel):
    """Chat message model"""
    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "agg_ai"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.chats.id", ondelete="CASCADE"), nullable=False)
    model_id = Column(Integer, ForeignKey("agg_ai.ai_provider_models.id", ondelete="SET NULL"), nullable=True)
    
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    attachments = Column(ARRAY(PGUUID(as_uuid=True)), nullable=True)
    
    chat = relationship("Chat", back_populates="messages", lazy="noload")
    model = relationship("AiProviderModel", lazy="noload") # we don't need have all messages that are associated with a model, so we don't have a back_populates
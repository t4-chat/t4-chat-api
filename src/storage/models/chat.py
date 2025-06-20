import uuid

from sqlalchemy import ARRAY, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import backref, relationship

from src.storage.models.base import BaseModel


class Chat(BaseModel):
    """Chat conversation model"""
    __tablename__ = "chats"
    __table_args__ = {"schema": "agg_ai"}

    user_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)
    pinned = Column(Boolean, nullable=False, default=False)
    
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan", lazy="noload")
    user = relationship("User", back_populates="chats", lazy="noload")
    shared_conversation = relationship("SharedConversation", uselist=False, back_populates="chat", lazy="noload")


class ChatMessage(BaseModel):
    """Chat message model"""
    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "agg_ai"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.chats.id", ondelete="CASCADE"), nullable=False)
    model_id = Column(PGUUID, ForeignKey("agg_ai.ai_provider_models.id", ondelete="SET NULL"),
                      nullable=True)  # default model id is for the message text itself

    image_gen_model_id = Column(PGUUID, ForeignKey("agg_ai.ai_provider_models.id", ondelete="SET NULL"), nullable=True)
    
    previous_message_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.chat_messages.id", ondelete="SET NULL"), nullable=True)
    
    seq_num = Column(Integer, nullable=False)
    
    role = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    selected = Column(Boolean, nullable=True)
    attachments = Column(ARRAY(PGUUID(as_uuid=True)), nullable=True)
    
    chat = relationship("Chat", back_populates="messages", lazy="noload")
    model = relationship("AiProviderModel", foreign_keys=[model_id],
                         lazy="noload")  # we don't need have all messages that are associated with a model, so we don't have a back_populates
    image_gen_model = relationship("AiProviderModel", foreign_keys=[image_gen_model_id], lazy="noload")
    previous_message = relationship("ChatMessage", remote_side=[id], lazy="noload")
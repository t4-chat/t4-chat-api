import uuid

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import Base


class Usage(Base):
    __tablename__ = "usage"
    __table_args__ = {"schema": "agg_ai"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.users.id"))
    model_id = Column(Integer, ForeignKey("agg_ai.ai_provider_models.id"))

    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)

    user = relationship("User", back_populates="usage", lazy="noload")
    model = relationship("AiProviderModel", lazy="noload")

from sqlalchemy import ARRAY, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class AiProviderModel(BaseModel):
    __tablename__ = "ai_provider_models"
    __table_args__ = {"schema": "agg_ai"}

    name = Column(String, nullable=False)  # this is what the user sees
    
    provider_id = Column(
        PGUUID(as_uuid=True), ForeignKey("agg_ai.ai_providers.id", ondelete="CASCADE")
    )

    prompt_path = Column(String, nullable=False)  # TODO: may be nullable for non LLM models

    price_input_token = Column(Float, nullable=False)  # TODO: may be nullable for non LLM models
    price_output_token = Column(Float, nullable=False)  # TODO: may be nullable for non LLM models
    context_length = Column(Integer, nullable=False)  # TODO: may be nullable for non LLM models

    is_active = Column(Boolean, nullable=False, default=True)
    tags = Column(ARRAY(String), nullable=False, default=[])

    modalities = Column(ARRAY(String), nullable=False, default=[])  # text, image, audio, vision, video

    provider = relationship("AiProvider", back_populates="models", lazy="noload")
    host_associations = relationship("ModelHostAssociation", back_populates="model", cascade="all, delete-orphan", lazy="noload")
    hosts = relationship("ModelHost", secondary="agg_ai.model_host_associations", lazy="noload", overlaps="host_associations")
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class AiProviderModel(BaseModel):
    __tablename__ = "ai_provider_models"
    __table_args__ = {"schema": "agg_ai"}

    name = Column(String, nullable=False)  # this is what the user sees
    slug = Column(
        String, nullable=False
    )  # this is what we need to use to call the model

    provider_id = Column(
        Integer, ForeignKey("agg_ai.ai_providers.id", ondelete="CASCADE")
    )

    host_id = Column(Integer, ForeignKey("agg_ai.model_hosts.id", ondelete="CASCADE"))

    prompt_path = Column(String, nullable=False)

    price_input_token = Column(Float, nullable=False)
    price_output_token = Column(Float, nullable=False)
    context_length = Column(Integer, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)

    provider = relationship("AiProvider", back_populates="models", lazy="noload")
    host = relationship("ModelHost", back_populates="models", lazy="noload")
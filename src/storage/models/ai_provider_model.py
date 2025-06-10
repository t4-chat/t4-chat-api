from sqlalchemy import ARRAY, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class AiProviderModel(BaseModel):
    __tablename__ = "ai_provider_models"
    __table_args__ = {"schema": "ai_providers"}

    name = Column(String, nullable=False)
    provider_id = Column(Integer, ForeignKey("ai_providers.ai_providers.id", ondelete="CASCADE"))
    modalities = Column(ARRAY(String), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    price_input_token = Column(Float, nullable=False)
    price_output_token = Column(Float, nullable=False)
    context_length = Column(Integer, nullable=False)
    provider = relationship("AiProvider", back_populates="models")

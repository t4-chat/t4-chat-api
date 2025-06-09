from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class AiProviderModel(BaseModel):
    __tablename__ = "ai_provider_models"
    __table_args__ = {'schema': 'ai_providers'}

    name = Column(String, nullable=False)
    provider_id = Column(Integer, ForeignKey("ai_providers.ai_providers.id", ondelete="CASCADE"))
    provider = relationship("AiProvider", back_populates="models")

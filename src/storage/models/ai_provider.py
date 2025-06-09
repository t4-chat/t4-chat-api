from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from base import BaseModel

class AiProvider(BaseModel):
    __tablename__ = "ai_providers"

    name = Column(String, nullable=False)
    models = relationship("AiProviderModel", back_populates="provider", cascade="all, delete-orphan")

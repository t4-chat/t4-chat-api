from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class AiProvider(BaseModel):
    __tablename__ = "ai_providers"
    __table_args__ = {"schema": "agg_ai"}

    name = Column(String, nullable=False)
    
    slug = Column(String, nullable=False)

    base_url = Column(String, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)

    models = relationship("AiProviderModel", back_populates="provider", cascade="all, delete-orphan")

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class Prompt(BaseModel):
    __tablename__ = "prompts"
    __table_args__ = {"schema": "agg_ai"}

    prompt = Column(String, nullable=False)

    models = relationship("AiProviderModel", back_populates="prompt")

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class ModelHostAssociation(BaseModel):
    __tablename__ = "model_host_associations"
    __table_args__ = {"schema": "agg_ai"}

    model_id = Column(
        PGUUID(as_uuid=True), ForeignKey("agg_ai.ai_provider_models.id", ondelete="CASCADE"), nullable=False
    )
    host_id = Column(
        PGUUID(as_uuid=True), ForeignKey("agg_ai.model_hosts.id", ondelete="CASCADE"), nullable=False
    )
    model_slug = Column(String, nullable=False) # for different hosts, the same model can have different slugs
    
    priority = Column(Integer, nullable=False, default=0)
    
    model = relationship("AiProviderModel", back_populates="host_associations", lazy="noload", overlaps="hosts,models")
    host = relationship("ModelHost", back_populates="model_associations", lazy="noload", overlaps="hosts,models")
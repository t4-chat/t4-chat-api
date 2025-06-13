import uuid
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel

class Limits(BaseModel):
    __tablename__ = "limits"
    __table_args__ = {"schema": "agg_ai"}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(Integer, ForeignKey("agg_ai.ai_provider_models.id"), nullable=True) # limit may not be per model, but rather per host
    
    # TODO: add host here, to limit per host
    max_tokens = Column(Integer, nullable=False)
    
    # Relationships
    user_group_associations = relationship("UserGroupLimits", back_populates="limits", lazy="noload")
    user_groups = relationship("UserGroup", secondary="agg_ai.user_group_limits", viewonly=True, lazy="noload")
    
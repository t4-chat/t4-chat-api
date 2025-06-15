from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class ModelHost(BaseModel):
    __tablename__ = "model_hosts"
    __table_args__ = {"schema": "agg_ai"}

    name = Column(String, nullable=False)
    
    slug = Column(String, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)

    model_associations = relationship("ModelHostAssociation", back_populates="host", cascade="all, delete-orphan", lazy="noload", overlaps="hosts")
    models = relationship("AiProviderModel", secondary="agg_ai.model_host_associations", lazy="noload", overlaps="host_associations,hosts,model_associations")

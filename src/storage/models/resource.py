import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class Resource(BaseModel):
    __tablename__ = "resources"
    __table_args__ = {"schema": "agg_ai"}

    user_id = Column(
        PGUUID(as_uuid=True), ForeignKey("agg_ai.users.id"), nullable=False
    )
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    storage_path = Column(String, nullable=False, unique=True)
    user = relationship("User", lazy="noload")

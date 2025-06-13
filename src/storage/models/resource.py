import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from src.storage.models.base import BaseModel


class Resource(BaseModel):
    __tablename__ = "resources"
    __table_args__ = {"schema": "agg_ai"}

    # Override the default integer id with UUID
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User who owns this resource
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.users.id"), nullable=False)

    # Original filename
    filename = Column(String, nullable=False)

    # Content type (MIME type)
    content_type = Column(String, nullable=False)

    # Path in cloud storage
    storage_path = Column(String, nullable=False, unique=True)

    # User that owns this resource
    user = relationship("User", lazy="noload")

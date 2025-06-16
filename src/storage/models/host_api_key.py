from sqlalchemy import Boolean, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class HostApiKey(BaseModel):
    __tablename__ = "host_api_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "host_id", name="uq_user_host_api_key"),
        {"schema": "agg_ai"}
    )

    user_id = Column(
        PGUUID(as_uuid=True), ForeignKey("agg_ai.users.id", ondelete="CASCADE"), nullable=False
    )
    host_id = Column(
        PGUUID(as_uuid=True), ForeignKey("agg_ai.model_hosts.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    encrypted_key = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    user = relationship("User", lazy="noload")
    host = relationship("ModelHost", lazy="noload")
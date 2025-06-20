from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class UserGroupLimits(BaseModel):
    __tablename__ = "user_group_limits"
    __table_args__ = (
        UniqueConstraint("user_group_id", "limits_id", name="uq_user_group_limits"),
        {"schema": "agg_ai"},
    )

    user_group_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.user_group.id"))
    limits_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.limits.id"))

    user_group = relationship(
        "UserGroup", back_populates="limits_associations", lazy="noload"
    )
    limits = relationship(
        "Limits", back_populates="user_group_associations", lazy="noload"
    )

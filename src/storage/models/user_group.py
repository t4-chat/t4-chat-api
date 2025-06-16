from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class UserGroup(BaseModel):
    __tablename__ = "user_group"
    __table_args__ = (
        UniqueConstraint("name", name="uq_user_group_name"),
        {"schema": "agg_ai"}
    )

    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)

    # Relationships
    users = relationship(
        "User", back_populates="user_group", cascade="all, delete-orphan", lazy="noload"
    )
    limits_associations = relationship(
        "UserGroupLimits", back_populates="user_group", lazy="noload"
    )
    limits = relationship(
        "Limits", secondary="agg_ai.user_group_limits", viewonly=True, lazy="noload"
    )

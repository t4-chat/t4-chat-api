from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class UserGroup(BaseModel):
    __tablename__ = "user_group"
    __table_args__ = {"schema": "agg_ai"}
    # Override the primary key from BaseModel
    __mapper_args__ = {"primary_key": ["name"]}

    id = None

    name = Column(String, primary_key=True)

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

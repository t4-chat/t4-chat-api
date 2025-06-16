from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from src.storage.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = {"schema": "agg_ai"}

    group_id = Column(PGUUID(as_uuid=True), ForeignKey("agg_ai.user_group.id"), nullable=False)

    email = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)

    chats = relationship(
        "Chat", back_populates="user", cascade="all, delete-orphan", lazy="noload"
    )
    usage = relationship(
        "Usage", back_populates="user", cascade="all, delete-orphan", lazy="noload"
    )
    user_group = relationship("UserGroup", back_populates="users", lazy="noload")

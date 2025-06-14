from sqlalchemy import Column, String

from src.storage.models.base import BaseModel

class WhiteList(BaseModel):
    __tablename__ = "white_list"
    __table_args__ = {"schema": "agg_ai"}

    email = Column(String, nullable=False)
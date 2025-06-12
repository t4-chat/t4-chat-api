from sqlalchemy import Column, Float

from src.storage.models.base import BaseModel


class Budget(BaseModel):
    """
    This is a temporary budgeting solution, to make sure we don't exceed the limits.
    """
    __tablename__ = "budget"
    __table_args__ = {"schema": "agg_ai"}
    
    budget = Column(Float, nullable=False)
    usage = Column(Float, nullable=False)


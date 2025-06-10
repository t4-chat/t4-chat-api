from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        from_attributes = True 
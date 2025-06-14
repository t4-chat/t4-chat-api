from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the user")
    email: str = Field(..., description="The email of the user")
    first_name: Optional[str] = Field(None, description="The first name of the user")
    last_name: Optional[str] = Field(None, description="The last name of the user")
    profile_image_url: Optional[str] = Field(
        None, description="The profile image url of the user"
    )

    class Config:
        from_attributes = True

from uuid import UUID

from pydantic import BaseModel


class UserGroupDTO(BaseModel):
    id: UUID
    name: str
    type: str

    class Config:
        from_attributes = True


class UserDTO(BaseModel):
    id: UUID
    email: str

    profile_image_url: str
    first_name: str
    last_name: str

    user_group: UserGroupDTO

    class Config:
        from_attributes = True

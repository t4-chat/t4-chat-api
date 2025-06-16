from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class HostApiKeyDTO(BaseModel):
    id: UUID
    user_id: UUID
    host_id: UUID
    
    name: str
    encrypted_key: str
    
    is_active: bool
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateHostApiKeyDTO(BaseModel):
    host_id: UUID
    name: str
    api_key: str


class UpdateHostApiKeyDTO(BaseModel):
    name: str | None = None
    api_key: str | None = None
    is_active: bool | None = None 
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HostApiKeyCreateSchema(BaseModel):
    host_id: UUID = Field(..., description="The ID of the model host")
    name: str = Field(..., description="User-friendly name for the API key")
    api_key: str = Field(..., description="The API key to be encrypted and stored")


class HostApiKeyUpdateSchema(BaseModel):
    name: str | None = Field(None, description="User-friendly name for the API key")
    api_key: str | None = Field(None, description="The API key to be encrypted and stored")
    is_active: bool | None = Field(None, description="Whether the API key is active")


class HostApiKeyResponseSchema(BaseModel):
    id: UUID = Field(..., description="The ID of the API key record")
    host_id: UUID = Field(..., description="The ID of the model host")
    name: str = Field(..., description="User-friendly name for the API key")
    is_active: bool = Field(..., description="Whether the API key is active")
    created_at: datetime = Field(..., description="When the API key was created")
    updated_at: datetime = Field(..., description="When the API key was last updated")

    class Config:
        from_attributes = True
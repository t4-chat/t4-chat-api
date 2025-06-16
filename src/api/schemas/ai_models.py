from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AiProviderResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the provider")
    name: str = Field(..., description="The name of the provider")
    slug: str = Field(..., description="The slug of the provider")

    class Config:
        from_attributes = True


class ModelHostAssociationSchema(BaseModel):
    host_id: UUID = Field(..., description="The id of the host")
    priority: int = Field(..., description="The priority of the host")

    class Config:
        from_attributes = True


class AiModelResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the model")
    name: str = Field(..., description="The name of the model")
    tags: List[str] = Field(..., description="The tags of the model")
    provider: Optional[AiProviderResponseSchema] = Field(None, description="The provider of the model")

    class Config:
        from_attributes = True


class EditAiModelRequestSchema(BaseModel):
    name: str = Field(..., description="The name of the model")
    slug: str = Field(..., description="The slug of the model")
    provider_id: UUID = Field(..., description="The id of the provider")
    prompt_path: str = Field(..., description="The path to the prompt")
    price_input_token: float = Field(..., description="The price of the input token")
    price_output_token: float = Field(..., description="The price of the output token")
    context_length: int = Field(..., description="The context length")
    is_active: bool = Field(..., description="Whether the model is active")
    tags: List[str] = Field(..., description="The tags of the model")
    host_associations: List[ModelHostAssociationSchema] = Field(..., description="The model host associations of the model")


class HostAiModelAssociationSchema(BaseModel):
    model_id: UUID = Field(..., description="The id of the model")
    priority: int = Field(..., description="The priority of the model")


class AiModelHostResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the host")
    name: str = Field(..., description="The name of the host")
    slug: str = Field(..., description="The slug of the host")
    priority: Optional[int] = Field(None, description="The priority of the host")
    is_active: bool = Field(..., description="Whether the host is active")
    model_associations: List[HostAiModelAssociationSchema] = Field([], description="The model associations of the host")
    
    class Config:
        from_attributes = True


class AiModelResponseForAdminSchema(BaseModel):
    id: UUID = Field(..., description="The id of the model")
    name: str = Field(..., description="The name of the model")
    slug: str = Field(..., description="The slug of the model")
    prompt_path: str = Field(..., description="The path to the prompt")
    price_input_token: float = Field(..., description="The price of the input token")
    price_output_token: float = Field(..., description="The price of the output token")
    context_length: int = Field(..., description="The context length")
    is_active: bool = Field(..., description="Whether the model is active")
    tags: List[str] = Field(..., description="The tags of the model")
    provider: Optional[AiProviderResponseSchema] = Field(None, description="The provider of the model")
    hosts: List[AiModelHostResponseSchema] = Field([], description="The hosts of the model")

    class Config:
        from_attributes = True


class EditAiModelHostRequestSchema(BaseModel):
    name: str = Field(..., description="The name of the host")
    slug: str = Field(..., description="The slug of the host")
    is_active: bool = Field(..., description="Whether the host is active")
    model_associations: List[HostAiModelAssociationSchema] = Field(..., description="The model associations of the host")

    class Config:
        from_attributes = True

from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, model_validator


class ModelHostDTO(BaseModel):
    id: UUID
    name: str
    slug: str
    priority: Optional[int] = None
    is_active: bool
    model_slug: Optional[str] = None  # The slug used for this model on this host
    model_associations: Optional[List["HostAiModelAssociationDTO"]] = []

    class Config:
        from_attributes = True


class AiProviderDTO(BaseModel):
    id: UUID
    name: str
    slug: str

    models: List["AiProviderModelDTO"] = []

    class Config:
        from_attributes = True


class AiProviderModelDTO(BaseModel):
    id: UUID
    name: str

    price_input_token: float
    price_output_token: float
    context_length: int
    is_active: bool
    prompt_path: str
    provider: Optional[AiProviderDTO]
    hosts: Optional[List[ModelHostDTO]]
    tags: List[str]
    has_api_key: bool = False
    modalities: List[str]
    
    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def sort_hosts_by_priority(cls, data: Any) -> Any:
        # If this is already a dict (like from direct construction), return as is
        if isinstance(data, dict):
            return data

        if data.provider is None:
            provider_data = None
        else:
            provider_data = {
                "id": data.provider.id,
                "name": data.provider.name,
                "slug": data.provider.slug,
            }

        keyed_hosts = {host.id: host for host in data.hosts}

        # Sort host associations by priority and convert to DTOs
        hosts_data = []
        for assoc in sorted(data.host_associations, key=lambda a: a.priority):
            host = keyed_hosts[assoc.host_id]
            hosts_data.append(
                {
                    "id": host.id,
                    "name": host.name,
                    "slug": host.slug,
                    "priority": assoc.priority,
                    "is_active": host.is_active,
                    "model_slug": assoc.model_slug,  # Include model_slug from association
                }
            )

        # Return a dictionary that Pydantic can use to construct the model
        # TODO: fix this
        return {
            "id": data.id,
            "name": data.name,
            "price_input_token": data.price_input_token,
            "price_output_token": data.price_output_token,
            "context_length": data.context_length,
            "is_active": data.is_active,
            "prompt_path": data.prompt_path,
            "provider": provider_data,
            "hosts": hosts_data,
            "tags": data.tags,
            "modalities": data.modalities,
        }


class ModelHostAssociationDTO(BaseModel):
    host_id: UUID
    model_slug: str
    priority: int

    class Config:
        from_attributes = True


class EditAiModelDTO(BaseModel):
    name: str
    provider_id: UUID
    prompt_path: str
    price_input_token: float
    price_output_token: float
    context_length: int
    is_active: bool
    tags: List[str]
    modalities: List[str]
    host_associations: List[ModelHostAssociationDTO]

    class Config:
        from_attributes = True


class HostAiModelAssociationDTO(BaseModel):
    model_id: UUID
    model_slug: str
    priority: int

    class Config:
        from_attributes = True


class EditAiModelHostDTO(BaseModel):
    name: str
    slug: str
    is_active: bool
    model_associations: List[HostAiModelAssociationDTO]

    class Config:
        from_attributes = True


class AiModelsInputDTO(BaseModel):
    image_gen_model_id: Optional[UUID] = None


class AiModelsModalitiesDTO(BaseModel):
    llm: Optional[AiProviderModelDTO] = None
    image_gen: Optional[AiProviderModelDTO] = None

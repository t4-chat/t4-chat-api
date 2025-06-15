from typing import Any, List

from pydantic import BaseModel, model_validator


class ModelHostDTO(BaseModel):
    id: int
    name: str
    slug: str
    priority: int
    
    class Config:
        from_attributes = True


class AiProviderDTO(BaseModel):
    id: int
    name: str
    slug: str
    
    models: List["AiProviderModelDTO"] = []

    class Config:
        from_attributes = True


class AiProviderModelDTO(BaseModel):
    id: int
    name: str
    slug: str
    
    price_input_token: float
    price_output_token: float

    prompt_path: str
    provider: AiProviderDTO
    hosts: List[ModelHostDTO]

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def sort_hosts_by_priority(cls, data: Any) -> Any:
        # If this is already a dict (like from direct construction), return as is
        if isinstance(data, dict):
            return data
            
        # Extract provider data
        provider_data = {
            'id': data.provider.id,
            'name': data.provider.name,
            'slug': data.provider.slug,
        }
        
        keyed_hosts = {host.id: host for host in data.hosts}
        
        # Sort host associations by priority and convert to DTOs
        hosts_data = []
        for assoc in sorted(data.host_associations, key=lambda a: a.priority):
            host = keyed_hosts[assoc.host_id]
            hosts_data.append({
                'id': host.id,
                'name': host.name,
                'slug': host.slug,
                'priority': assoc.priority
            })
        
        # Return a dictionary that Pydantic can use to construct the model
        return {
            'id': data.id,
            'name': data.name,
            'slug': data.slug,
            'price_input_token': data.price_input_token,
            'price_output_token': data.price_output_token,
            'prompt_path': data.prompt_path,
            'provider': provider_data,
            'hosts': hosts_data
        }

from typing import List

from pydantic import BaseModel


class ModelHostDTO(BaseModel):
    id: int
    name: str
    slug: str
    
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
    host: ModelHostDTO

    class Config:
        from_attributes = True

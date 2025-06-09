from pydantic import BaseModel
from typing import List
from .ai_provider_model import AiProviderModelResponse

class AiProviderResponse(BaseModel):
    id: int
    name: str
    models: List[AiProviderModelResponse] = []

    class Config:
        from_attributes = True
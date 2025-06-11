from pydantic import BaseModel
from typing import List

class AiProviderModelResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class AiProviderResponse(BaseModel):
    id: int
    name: str
    slug: str
    models: List[AiProviderModelResponse] = []

    class Config:
        from_attributes = True
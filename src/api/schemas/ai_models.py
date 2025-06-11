from pydantic import BaseModel, Field

class AiProviderResponse(BaseModel):
    id: int
    name: str
    slug: str

class AiModelResponse(BaseModel):
    id: int
    name: str
    provider: AiProviderResponse

    class Config:
        from_attributes = True

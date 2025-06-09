from pydantic import BaseModel

class AiProviderModelResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
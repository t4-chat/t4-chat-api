from pydantic import BaseModel, Field


class AiProviderResponseSchema(BaseModel):
    id: int = Field(..., description="The id of the provider")
    name: str = Field(..., description="The name of the provider")
    slug: str = Field(..., description="The slug of the provider")

    class Config:
        from_attributes = True


class AiModelResponseSchema(BaseModel):
    id: int = Field(..., description="The id of the model")
    name: str = Field(..., description="The name of the model")
    provider: AiProviderResponseSchema = Field(
        ..., description="The provider of the model"
    )

    class Config:
        from_attributes = True

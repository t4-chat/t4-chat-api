from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class AiProviderModelResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the model")
    name: str = Field(..., description="The name of the model")

    class Config:
        from_attributes = True


class AiProviderResponseSchema(BaseModel):
    id: UUID = Field(..., description="The id of the provider")
    name: str = Field(..., description="The name of the provider")
    slug: str = Field(..., description="The slug of the provider")
    models: List[AiProviderModelResponseSchema] = Field(
        ..., description="The models of the provider"
    )

    class Config:
        from_attributes = True

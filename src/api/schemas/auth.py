from pydantic import BaseModel, Field


class GoogleAuthRequestSchema(BaseModel):
    token: str = Field(..., description="The token from Google")


class TokenResponseSchema(BaseModel):
    access_token: str = Field(..., description="The access token")

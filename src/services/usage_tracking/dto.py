from uuid import UUID

from pydantic import BaseModel


class UsageDTO(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    model_id: int
    user_id: UUID

    class Config:
        from_attributes = True

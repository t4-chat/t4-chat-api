from pydantic import BaseModel


class TextGenerationResponse(BaseModel):
    """Response from text generation"""
    text: str 
from pydantic import BaseModel, Field


class DefaultResponseGenerationOptions(BaseModel):
    """Options for text generation"""
    temperature: float = Field(
        default=0.7,
        description="Controls randomness. Higher values (e.g., 0.8) make output more random, lower values (e.g., 0.2) make it more deterministic.",
        ge=0.0,
        le=1.0
    )
    max_tokens: int = Field(
        default=1000,
        description="Maximum number of tokens to generate in the response.",
        gt=0
    )
    # Add more common parameters as needed 
from typing import Optional
from pydantic import BaseModel

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
class StreamGenerationResponse(BaseModel):
    text: str
    usage: Optional[Usage] = None


class TextGenerationResponse(BaseModel):
    text: str
    usage: Usage = None
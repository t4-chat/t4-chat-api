from uuid import UUID
from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    file_id: UUID = Field(..., description="The id of the file")
    filename: str = Field(..., description="The name of the file")
    content_type: str = Field(..., description="The content type of the file")
    
class FileDataResponse(FileResponse):
    data: bytes
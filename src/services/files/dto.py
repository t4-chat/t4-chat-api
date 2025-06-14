from uuid import UUID

from pydantic import BaseModel


class FileDTO(BaseModel):
    file_id: UUID
    filename: str
    content_type: str


class FileDataDTO(FileDTO):
    data: bytes

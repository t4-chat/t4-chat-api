from typing import Any, Dict
import uuid

from src.services.cloud_storage_service import CloudStorageService
from src.services import utils

class FilesService:
    def __init__(self, cloud_storage_service: CloudStorageService):
        self.cloud_storage_service = cloud_storage_service
        
    def _get_file_path(self, filename: str, content_type: str) -> str:
        return f"{utils.get_attachment_type(content_type)}/{uuid.uuid4()}_{filename}"

    async def upload_file(self, user_id: str, filename: str, content_type: str, contents: bytes) -> str:
        return await self.cloud_storage_service.upload_file(f"attachments/{user_id}/{self._get_file_path(filename, content_type)}", contents, {"content_type": content_type})

    async def get_file(self, file_id: str) -> Dict[str, Any]:
        file_data = await self.cloud_storage_service.get_file(file_id)
        metadata = await self.cloud_storage_service.get_file_metadata(file_id)
        return {
            "data": file_data,
            "metadata": metadata
        }

    async def delete_file(self, file_id: str):
        return await self.cloud_storage_service.delete_file(file_id)

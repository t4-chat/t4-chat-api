import uuid
from typing import Any, Dict

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.files import FileDataResponse, FileResponse
from src.services import utils
from src.services.cloud_storage_service import CloudStorageService
from src.services.context import Context
from src.services.errors import errors
from src.storage.models.resource import Resource


class FilesService:
    def __init__(self, context: Context = None, cloud_storage_service: CloudStorageService = None, db: AsyncSession = None):
        self.context = context
        self.cloud_storage_service = cloud_storage_service
        self.db = db

    def _get_file_path(self, file_id: uuid.UUID, filename: str, content_type: str) -> str:
        return f"{utils.get_attachment_type(content_type)}/{file_id}_{filename}"

    async def upload_file(self, filename: str, content_type: str, contents: bytes) -> FileResponse:
        file_id = uuid.uuid4()
        file_path = self._get_file_path(file_id, filename, content_type)

        async with self.db.begin():
            await self.db.execute(insert(Resource).values(id=file_id, user_id=self.context.user_id, filename=filename, content_type=content_type, storage_path=file_path))
        
        await self.cloud_storage_service.upload_file(f"attachments/{self.context.user_id}/{file_path}", contents, {"content_type": content_type, "file_name": filename})
        return FileResponse(file_id=file_id, filename=filename, content_type=content_type)

    async def get_file(self, file_id: str) -> FileDataResponse:
        resource = await self.db.execute(select(Resource).where(Resource.id == file_id, Resource.user_id == self.context.user_id))
        resource = resource.scalar_one_or_none()
        if not resource:
            raise errors.NotFoundError(f"File with id {file_id} not found")
            
        storage_path = resource.storage_path
        content_type = resource.content_type
        
        file_data = await self.cloud_storage_service.get_file(f"attachments/{self.context.user_id}/{storage_path}")
        return FileDataResponse(file_id=file_id, filename=file_data["metadata"].get("file_name", str(file_id)), content_type=content_type, data=file_data["data"])

    async def delete_file(self, file_id: str):
        resource = await self.db.execute(select(Resource).where(Resource.id == file_id, Resource.user_id == self.context.user_id))
        resource = resource.scalar_one_or_none()
        if not resource:
            raise errors.NotFoundError(f"File with id {file_id} not found")
            
        storage_path = resource.storage_path
        
        return await self.cloud_storage_service.delete_file(f"attachments/{self.context.user_id}/{storage_path}")

import uuid
from typing import Any, Dict

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def upload_file(self, filename: str, content_type: str, contents: bytes) -> str:
        file_id = uuid.uuid4()

        file_path = self._get_file_path(file_id, filename, content_type)
        
        await self.db.execute(insert(Resource).values(id=file_id, user_id=self.context.user_id, filename=filename, content_type=content_type, storage_path=file_path))

        await self.cloud_storage_service.upload_file(f"attachments/{self.context.user_id}/{file_path}", contents, {"content_type": content_type})
        await self.db.commit()
        return file_id

    async def get_file(self, file_id: str) -> Dict[str, Any]:
        resource = await self.db.execute(select(Resource).where(Resource.id == file_id, Resource.user_id == self.context.user_id))
        resource = resource.scalar_one_or_none()
        if not resource:
            raise errors.NotFoundError(f"File with id {file_id} not found")
        file_data = await self.cloud_storage_service.get_file(f"attachments/{self.context.user_id}/{resource.storage_path}")
        return {"data": file_data["data"], "metadata": {"content_type": resource.content_type}}

    async def delete_file(self, file_id: str):
        resource = await self.db.execute(select(Resource).where(Resource.id == file_id, Resource.user_id == self.context.user_id))
        resource = resource.scalar_one_or_none()
        if not resource:
            raise errors.NotFoundError(f"File with id {file_id} not found")

        return await self.cloud_storage_service.delete_file(f"attachments/{self.context.user_id}/{resource.storage_path}")

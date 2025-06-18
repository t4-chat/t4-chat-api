import uuid
from typing import Optional

from sqlalchemy import and_

from src.services.common import errors
from src.services.common.context import Context
from src.services.files import utils
from src.services.files.cloud_storage_service import CloudStorageService
from src.services.files.dto import FileDataDTO, FileDTO

from src.storage.base_repo import BaseRepository
from src.storage.models.resource import Resource


class FilesService:
    def __init__(
        self,
        context: Context = None,
        cloud_storage_service: CloudStorageService = None,
        resource_repo: BaseRepository[Resource] = None,
    ):
        self.context = context
        self.cloud_storage_service = cloud_storage_service
        self.resource_repo = resource_repo

    def _get_file_path(
        self, file_id: uuid.UUID, filename: str, content_type: str
    ) -> str:
        return f"{utils.get_attachment_type(content_type)}/{file_id}_{filename}"

    async def upload_file(
            self, contents: bytes, content_type: str, filename: Optional[str] = None
    ) -> FileDTO:
        file_id = uuid.uuid4()
        file_path = self._get_file_path(file_id, filename, content_type)

        # TODO: refactor this
        if not filename:
            filename = utils.generate_random_filename()

        resource = Resource(
            id=file_id,
            user_id=self.context.user_id,
            filename=filename,
            content_type=content_type,
            storage_path=file_path,
        )

        resource = await self.resource_repo.add(resource)

        await self.cloud_storage_service.upload_file(
            f"attachments/{self.context.user_id}/{file_path}",
            contents,
            {"content_type": content_type, "file_name": filename},
        )
        return FileDTO(file_id=file_id, filename=filename, content_type=content_type)

    async def get_file(self, file_id: str) -> FileDataDTO:
        filter = and_(Resource.id == file_id, Resource.user_id == self.context.user_id)
        resource = await self.resource_repo.get(filter=filter)

        if not resource:
            raise errors.NotFoundError(f"File with id {file_id} not found")

        storage_path = resource.storage_path
        content_type = resource.content_type

        file_data = await self.cloud_storage_service.get_file(
            f"attachments/{self.context.user_id}/{storage_path}"
        )
        return FileDataDTO(
            file_id=file_id,
            filename=file_data["metadata"].get("file_name", str(file_id)),
            content_type=content_type,
            data=file_data["data"],
        )

    async def delete_file(self, file_id: str):
        filter = and_(Resource.id == file_id, Resource.user_id == self.context.user_id)
        resource = await self.resource_repo.get(filter=filter)

        if not resource:
            raise errors.NotFoundError(f"File with id {file_id} not found")

        storage_path = resource.storage_path

        await self.cloud_storage_service.delete_file(
            f"attachments/{self.context.user_id}/{storage_path}"
        )
        await self.resource_repo.delete(resource)

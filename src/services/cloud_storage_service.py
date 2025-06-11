from contextvars import Context
from google.cloud import storage

from src.config import settings

# TODO: rework to async
class CloudStorageService:
    def __init__(self, context: Context):
        self.context = context

        self.client = storage.Client()
        self.bucket = self.client.bucket(settings.GCP_BUCKET_NAME)

    async def upload_file(self, path: str, contents: bytes, metadata: dict = None) -> str:
        blob = self.bucket.blob(path)

        # Upload the file contents
        blob.upload_from_string(contents)

        # Set metadata if provided
        if metadata:
            blob.metadata = metadata
            blob.patch()

        return path

    async def get_file(self, path: str) -> dict:
        blob = self.bucket.blob(path)
        return {
            "data": blob.download_as_bytes(),
            "metadata": blob.metadata or {}
        }

    async def delete_file(self, path: str) -> bool:
        blob = self.bucket.blob(path)
        try:
            blob.delete()
            return True
        except Exception:
            return False

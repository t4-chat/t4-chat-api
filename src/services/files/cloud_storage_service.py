import asyncio
from contextvars import Context

from google.cloud import storage

from src.config import settings


# TODO: rework to async
class CloudStorageService:
    def __init__(self, context: Context):
        self.context = context

        self.client = storage.Client()
        self.bucket = self.client.bucket(settings.GCP_BUCKET_NAME)

    async def upload_file(
        self, path: str, contents: bytes, metadata: dict = None
    ) -> str:
        blob = self.bucket.blob(path)

        # Upload the file contents in a thread pool
        await asyncio.to_thread(blob.upload_from_string, contents)

        # Set metadata if provided
        if metadata:
            blob.metadata = metadata
            await asyncio.to_thread(blob.patch)

        return path

    async def get_file(self, path: str) -> dict:
        blob = self.bucket.blob(path)

        # Download data and get metadata in parallel
        data_task = asyncio.to_thread(blob.download_as_bytes)
        metadata_task = asyncio.to_thread(lambda: blob.metadata or {})

        data, metadata = await asyncio.gather(data_task, metadata_task)

        return {"data": data, "metadata": metadata}

    async def delete_file(self, path: str) -> bool:
        blob = self.bucket.blob(path)
        try:
            await asyncio.to_thread(blob.delete)
            return True
        except Exception:
            return False

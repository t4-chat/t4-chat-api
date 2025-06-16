from fastapi import APIRouter, File, Response, UploadFile

from src.api.schemas.files import FileResponseSchema
from src.containers.container import FilesServiceDep
from src.logging.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload", response_model=FileResponseSchema)
async def upload_file(
    files_service: FilesServiceDep,
    file: UploadFile = File(...),
) -> FileResponseSchema:
    contents = await file.read()
    resp = await files_service.upload_file(file.filename, file.content_type, contents)
    return resp


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    files_service: FilesServiceDep,
) -> Response:
    file_data = await files_service.get_file(file_id)
    response = Response(content=file_data.data, media_type=file_data.content_type)
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename={file_data.filename}"
    return response

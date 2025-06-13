from fastapi import APIRouter, File, UploadFile, Response

from src.logging.logging_config import get_logger
from src.containers.di import files_service
from src.api.schemas.files import FileResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    service: files_service,
    file: UploadFile = File(...),
):
    contents = await file.read()
    resp = await service.upload_file(file.filename, file.content_type, contents)
    return resp


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    service: files_service,
):
    file_data = await service.get_file(file_id)
    response = Response(
        content=file_data.data, 
        media_type=file_data.content_type
    )
    response.headers["Content-Disposition"] = f"attachment; filename={file_data.filename}"
    return response

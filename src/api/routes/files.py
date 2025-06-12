from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, File, UploadFile, Response

from src.containers.containers import AppContainer
from src.logging.logging_config import get_logger
from src.services.files_service import FilesService
from src.api.schemas.files import FileResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileResponse)
@inject
async def upload_file(
    file: UploadFile = File(...),
    service: FilesService = Depends(Provide[AppContainer.files_service]),
):
    contents = await file.read()
    resp = await service.upload_file(file.filename, file.content_type, contents)
    return resp


@router.get("/{file_id}")
@inject
async def get_file(
    file_id: str,
    service: FilesService = Depends(Provide[AppContainer.files_service]),
):
    file_data = await service.get_file(file_id)
    response = Response(
        content=file_data.data, 
        media_type=file_data.content_type
    )
    response.headers["Content-Disposition"] = f"attachment; filename={file_data.filename}"
    return response

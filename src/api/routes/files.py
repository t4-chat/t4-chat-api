from fastapi import APIRouter, UploadFile, File, Depends, Request
from dependency_injector.wiring import inject, Provide

from src.containers.containers import AppContainer
from src.services.files_service import FilesService

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
@inject
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    service: FilesService = Depends(Provide[AppContainer.files_service]),
):
    contents = await file.read()
    user_id = request.state.user_id
    file_id = await service.upload_file(user_id, file.filename, file.content_type, contents)
    return {"file_id": file_id}

from fastapi import APIRouter, UploadFile, File


router = APIRouter(prefix="/api/files", tags=["files"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename}
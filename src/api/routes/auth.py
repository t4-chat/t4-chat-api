from fastapi import APIRouter, HTTPException, status

from src.api.schemas.auth import GoogleAuthRequest, TokenResponse
from src.containers.di import auth_service

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/google", response_model=TokenResponse)
async def google_login(
    request: GoogleAuthRequest, 
    service: auth_service
):
    try:
        token = await service.authenticate_with_google(request.token)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

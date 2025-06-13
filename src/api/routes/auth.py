from fastapi import APIRouter, HTTPException, status

from src.api.schemas.auth import GoogleAuthRequest, TokenResponse
from src.containers.container import auth_service_dep

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/google", response_model=TokenResponse)
async def google_login(
    request: GoogleAuthRequest, 
    auth_service: auth_service_dep
):
    try:
        token = await auth_service.authenticate_with_google(request.token)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

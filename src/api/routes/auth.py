from fastapi import APIRouter, HTTPException, status, Depends
from dependency_injector.wiring import inject, Provide

from src.api.schemas.auth import GoogleAuthRequest, TokenResponse
from src.services.auth.auth_service import AuthService
from src.containers.containers import AppContainer

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/google", response_model=TokenResponse)
@inject
async def google_login(
    request: GoogleAuthRequest, 
    auth_service: AuthService = Depends(Provide[AppContainer.auth_service])
):
    try:
        token = await auth_service.authenticate_with_google(request.token)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

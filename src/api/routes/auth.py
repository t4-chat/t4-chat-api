from fastapi import APIRouter, HTTPException, status

from src.api.schemas.auth import GoogleAuthRequestSchema, TokenResponseSchema
from src.containers.container import AuthServiceDep

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/google", response_model=TokenResponseSchema)
async def google_login(
    request: GoogleAuthRequestSchema,
    auth_service: AuthServiceDep,
):
    try:
        token = await auth_service.authenticate_with_google(request.token)
        return TokenResponseSchema(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

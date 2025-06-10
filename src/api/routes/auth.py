from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from src.api.models.auth import GoogleAuthRequest, TokenResponse
from src.services.auth.auth_service import auth_service
from src.services.user_service import user_service
from src.storage.models.user import User

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/google", response_model=TokenResponse)
async def google_login(request: GoogleAuthRequest, auth_service: auth_service):
    try:
        token = auth_service.authenticate_with_google(request.token)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/test-user")
async def create_test_user(user_service: user_service):
    """
    Create a test user with a fixed ID for development purposes.
    This endpoint should only be available in development environments.
    """
    # Create test user with the specified UUID
    test_user_id = UUID('123e4567-e89b-12d3-a456-426614174000')
    
    # Generate token for this user
    user = User(id=test_user_id, email="test@test.com", first_name="Test", last_name="User")
    user_service.create_if_not_exists(user=user)
    
    return {"message": "Test user created", "user_id": test_user_id}


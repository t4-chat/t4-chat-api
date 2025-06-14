from fastapi import APIRouter, HTTPException, Request, status

from src.api.schemas.users import UserResponseSchema
from src.containers.container import UserServiceDep

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get("/current", response_model=UserResponseSchema)
async def get_current_user(
    request: Request,
    user_service: UserServiceDep,
):
    user_id = request.state.user_id
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found"
        )
        
    return user

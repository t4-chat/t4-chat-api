from fastapi import APIRouter, Request

from src.api.schemas.users import UserResponse
from src.containers.container import user_service

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get("/current", response_model=UserResponse)
async def get_current_user(
    request: Request, 
    service: user_service
):
    user_id = request.state.user_id
    user = await service.get_user_by_id(user_id)
    return user

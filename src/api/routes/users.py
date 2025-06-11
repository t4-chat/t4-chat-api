from fastapi import APIRouter, Request, Depends
from dependency_injector.wiring import inject, Provide

from src.api.schemas.users import UserResponse
from src.services.user_service import UserService
from src.containers.containers import AppContainer


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get("/current", response_model=UserResponse)
@inject
async def get_current_user(
    request: Request, 
    user_service: UserService = Depends(Provide[AppContainer.user_service])
):
    user_id = request.state.user_id
    user = await user_service.get_user_by_id(user_id)
    return user

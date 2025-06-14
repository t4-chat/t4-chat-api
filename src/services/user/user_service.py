from uuid import UUID

from src.services.common.context import Context
from src.services.common.enums import UserGroupName
from src.services.user.dto import UserDTO

from src.storage.base_repo import BaseRepository
from src.storage.models import User


class UserService:
    def __init__(self, context: Context = None, user_repo: BaseRepository[User] = None):
        self.context = context
        self.user_repo = user_repo

    async def create_if_not_exists(self, user: User) -> User:
        existing_user = await self.user_repo.get(filter=User.email == user.email)

        if existing_user:
            return existing_user

        # Assign default "basic" user group if no group_name is set
        if user.group_name is None:
            user.group_name = UserGroupName.BASIC

        user = await self.user_repo.add(user)
        return user

    async def get_user_by_id(self, user_id: UUID, **kwargs) -> UserDTO:
        includes = []

        if kwargs.get("user_group", False):
            includes.append(User.user_group)
        if kwargs.get("chats", False):
            includes.append(User.chats)
        if kwargs.get("usage", False):
            includes.append(User.usage)
        if kwargs.get("limits", False):
            includes.append(User.limits)

        return await self.user_repo.get(filter=User.id == user_id, includes=includes)

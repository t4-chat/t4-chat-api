from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.storage.models import User
from src.storage.models.user_group import UserGroup
from src.utils.enums import UserGroupName
from src.services.context import Context

class UserService:
    def __init__(self, context: Context = None, db: AsyncSession = None):
        self.context = context
        self.db = db
    
    async def create_if_not_exists(self, user: User) -> User:
        result = await self.db.execute(
            select(User).where(User.email == user.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return existing_user

        # Assign default "basic" user group if no group_name is set
        if user.group_name is None:
            user.group_name = UserGroupName.BASIC

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_user_by_id(self, user_id: UUID, **kwargs) -> User:
        query = select(User)
        if kwargs.get("user_group", False):
            query = query.options(selectinload(User.user_group))
        if kwargs.get("chats", False):
            query = query.options(selectinload(User.chats))
        if kwargs.get("usage", False):
            query = query.options(selectinload(User.usage))
        if kwargs.get("limits", False):
            query = query.options(selectinload(User.limits))
        
        
        result = await self.db.execute(query.where(User.id == user_id))
        return result.scalar_one_or_none()

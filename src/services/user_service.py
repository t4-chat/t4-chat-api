from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.storage.models import User
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

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_user_by_id(self, user_id: UUID) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

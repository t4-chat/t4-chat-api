from src.services.context import Context
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.storage.models.budget import Budget
from src.services.errors.errors import BudgetExceededError, NotFoundError
from src.config import settings


class BudgetService:
    def __init__(self, context: Context, db: AsyncSession):
        self.context = context
        self.db = db

    async def add_usage(self, usage: float) -> None:
        results = await self.db.execute(select(Budget).order_by(Budget.created_at.desc()).limit(1))
        budget = results.scalar_one_or_none()
        if not budget:
            raise NotFoundError("Budget", "No budget found")

        budget.usage += usage
        await self.db.commit()

        if budget.usage > budget.budget:
            raise BudgetExceededError("Budget exceeded")

    async def get_budget(self) -> Budget:
        results = await self.db.execute(select(Budget).order_by(Budget.created_at.desc()).limit(1))
        budget = results.scalar_one_or_none()
        if not budget:
            raise NotFoundError("Budget", "No budget found")
        return budget

    async def check_budget(self) -> None:
        budget = await self.get_budget()
        if budget.usage > budget.budget:
            raise BudgetExceededError("Budget exceeded")

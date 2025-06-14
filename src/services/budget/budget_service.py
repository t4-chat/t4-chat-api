from src.services.budget.dto import BudgetDTO
from src.services.common import errors
from src.services.common.context import Context
from src.services.common.decorators import convert_to_dto

from src.storage.base_repo import BaseRepository
from src.storage.models.budget import Budget


class BudgetService:
    def __init__(self, context: Context, budget_repo: BaseRepository[Budget]):
        self.context = context
        self.budget_repo = budget_repo

    async def add_usage(self, cost: float) -> None:
        budget = await self.budget_repo.get_first(order_by=Budget.created_at.desc())
        if not budget:
            raise errors.NotFoundError("Budget", "No budget found")

        budget.usage += cost
        await self.budget_repo.update(budget)

        if budget.usage > budget.budget:
            raise errors.BudgetExceededError("Budget exceeded")

    @convert_to_dto
    async def get_budget(self) -> BudgetDTO:
        budget = await self.budget_repo.get_first(order_by=Budget.created_at.desc())
        if not budget:
            raise errors.NotFoundError("Budget", "No budget found")
        return budget

    async def check_budget(self) -> None:
        if (budget := await self.get_budget()).usage > budget.budget:
            raise errors.BudgetExceededError("Budget exceeded")

from src.services.budget.budget_service import BudgetService
from src.services.common.context import get_context

from src.storage.base_repo import BaseRepository
from src.storage.db import db_session_manager
from src.storage.models import Budget


async def check_budget():
    """
    Dependency that checks if the budget has been exceeded.
    Uses its own database session to avoid conflicts with the endpoint handler.
    """
    # Create a new session for budget checking
    context = get_context()
    async with db_session_manager.session() as db:
        # Create a temporary budget service instance with its own session
        budget_repo = BaseRepository(Budget, db)
        budget_service = BudgetService(context=context, budget_repo=budget_repo)
        await budget_service.check_budget()
    return True

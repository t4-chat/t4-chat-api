from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from src.containers.containers import AppContainer
from src.services.budget_service import BudgetService
from src.storage.db import get_db


@inject
async def check_budget(
    container=Depends(Provide[AppContainer])
):
    """
    Dependency that checks if the budget has been exceeded.
    Uses its own database session to avoid conflicts with the endpoint handler.
    """
    # Create a new session for budget checking
    async with get_db() as db:
        # Create a temporary budget service instance with its own session
        budget_service = BudgetService(
            context=container.context(),
            db=db
        )
        await budget_service.check_budget()
    return True 
from dependency_injector.wiring import inject, Provide
from fastapi import Depends

from src.containers.containers import AppContainer
from src.services.budget_service import BudgetService


@inject
async def check_budget(
    container=Depends(Provide[AppContainer])
):
    """
    Dependency that checks if the budget has been exceeded.
    Uses its own database session to avoid conflicts with the endpoint handler.
    """
    # Create a new session for budget checking
    async with container.db_session_manager().session() as db:
        # Create a temporary budget service instance with its own session
        budget_service = BudgetService(
            context=container.context(),
            db=db
        )
        await budget_service.check_budget()
    return True
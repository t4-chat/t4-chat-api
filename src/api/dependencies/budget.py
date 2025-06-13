from src.services.budget_service import BudgetService
from src.services.context import get_context
from src.storage.database import db_session_manager


async def check_budget():
    """
    Dependency that checks if the budget has been exceeded.
    Uses its own database session to avoid conflicts with the endpoint handler.
    """
    # Create a new session for budget checking
    context = get_context()
    async with db_session_manager.session() as db:
        # Create a temporary budget service instance with its own session
        budget_service = BudgetService(
            context=context,
            db=db
        )
        await budget_service.check_budget()
    return True
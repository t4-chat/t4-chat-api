# This module is deprecated and no longer used with the new DI system
# We use get_db_session directly in di.py now

from starlette.requests import Request
from src.storage.database import db_session_manager
from src.logging.logging_config import get_logger


def create_db_session_middleware():
    """
    This middleware is kept for reference but is no longer used 
    since we use FastAPI's dependency injection directly.
    """
    logger = get_logger(__name__)
    
    async def db_session_middleware(request: Request, call_next):
        try:
            async with db_session_manager.session() as session:
                response = await call_next(request)
                return response
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            raise
            
    return db_session_middleware
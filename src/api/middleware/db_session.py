from dependency_injector import providers

from starlette.requests import Request
from src.containers.containers import AppContainer
from src.logging.logging_config import get_logger


def create_db_session_middleware(container: AppContainer):
    logger = get_logger(__name__)
    
    async def db_session_middleware(request: Request, call_next):
        db_session_manager = container.db_session_manager()
        
        try:
            async with db_session_manager.session() as session:
                with container.db.override(providers.Object(session)):
                    response = await call_next(request)
                return response
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            raise
            
    return db_session_middleware
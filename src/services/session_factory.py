from contextlib import contextmanager, asynccontextmanager
from typing import TypeVar, Type, Any


from src.storage.db import get_fresh_session

# Generic type for any service
T = TypeVar('T')

class SessionFactory:
    """
    Factory for creating service instances with fresh database sessions.
    Provides a clean way to create and manage service instances with their own DB sessions.
    """
    
    @staticmethod
    @asynccontextmanager
    async def create_service_with_session(service_class: Type[T], *args: Any, **kwargs: Any) -> T:
        """
        Create a service instance with a fresh database session.
        Handles session creation and cleanup automatically.
        
        Usage:
            async with SessionFactory.create_service_with_session(UsageTrackingService) as service:
                await service.track_usage(...)
        
        Args:
            service_class: The service class to instantiate
            *args, **kwargs: Additional arguments to pass to the service constructor
            
        Returns:
            An instance of the service with a fresh database session
        """
        db = await get_fresh_session()
        try:
            # Create the service with the fresh session
            service = service_class(db, *args, **kwargs)
            yield service
        except Exception:
            # Rollback transaction on error
            await db.rollback()
            raise
        finally:
            # Always clean up the session
            await db.close() 
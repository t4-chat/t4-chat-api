from contextlib import asynccontextmanager
from typing import TypeVar, Type, Any

from src.storage.db_context import db_session_context

# Generic type for any service
T = TypeVar('T')

class SessionFactory:
    """
    Factory for creating service instances with database sessions from the request context.
    Provides a clean way to create and manage service instances with their DB sessions.
    """
    
    @staticmethod
    @asynccontextmanager
    async def create_service_with_session(service_class: Type[T], *args: Any, **kwargs: Any) -> T:
        """
        Create a service instance with a database session from the request context.
        The session is managed by the request middleware.
        
        Usage:
            async with SessionFactory.create_service_with_session(UsageTrackingService) as service:
                await service.track_usage(...)
        
        Args:
            service_class: The service class to instantiate
            *args, **kwargs: Additional arguments to pass to the service constructor
            
        Returns:
            An instance of the service with a database session from the request context
        """
        try:
            # Get the session from the request context
            db = db_session_context.get()
            if db is None:
                raise RuntimeError("No database session available in context")
                
            # Create the service with the session from context
            service = service_class(db, *args, **kwargs)
            yield service
        except Exception:
            # Rollback transaction on error
            await db.rollback()
            raise 
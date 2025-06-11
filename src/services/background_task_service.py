from uuid import UUID
from litellm import Usage

from src.services.usage_tracking_service import UsageTrackingService
from src.services.session_factory import SessionFactory
from src.logging.logging_config import get_logger

# Set up logging
logger = get_logger(__name__)

class BackgroundTaskService:
    """
    Service for handling background tasks that require independent database sessions.
    This service uses SessionFactory to create services with fresh sessions.
    """
    
    def __init__(self):
        pass
        
    async def track_model_usage(self, user_id: UUID, model_id: int, usage: Usage):
        try:
            async with SessionFactory.create_service_with_session(UsageTrackingService) as usage_service:
                await usage_service.track_usage(user_id, model_id, usage)
        except Exception as e:
            logger.error(f"Error tracking model usage for user {user_id}, model {model_id}: {str(e)}", exc_info=True)
            # Re-raise the exception to ensure FastAPI knows the task failed
            raise 
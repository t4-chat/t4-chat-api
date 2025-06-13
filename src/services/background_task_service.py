from uuid import UUID
from litellm import Usage
import traceback
from src.services.context import Context
from src.services.usage_tracking_service import UsageTrackingService
from src.logging.logging_config import get_logger
from src.storage.db import get_db

# Set up logging
logger = get_logger(__name__)

class BackgroundTaskService:
    """
    Service for handling background tasks that require independent database sessions.
    This service uses SessionFactory to create services with fresh sessions.
    """
    
    def __init__(self, context: Context):
        self.context = context
        
    async def track_model_usage(self, user_id: UUID, model_id: int, usage: Usage):
        print("track_model_usage")
        # try:
        #     async with get_db() as session:
        #         usage_service = UsageTrackingService(self.context, session)
        #         await usage_service.track_usage(user_id, model_id, usage)
        # except Exception as e:
        #     logger.error(f"Error tracking model usage for user {user_id}, model {model_id}: {str(e)}", exc_info=True)
        #     self.context.logger.error(traceback.format_exc())
        #     # Re-raise the exception to ensure FastAPI knows the task failed
        #     raise e
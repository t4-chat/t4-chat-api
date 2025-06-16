import traceback
from uuid import UUID

from src.services.common.context import Context
from src.services.usage_tracking.dto import TokenUsageDTO
from src.services.usage_tracking.usage_tracking_service import UsageTrackingService

from src.storage.base_repo import BaseRepository
from src.storage.db import db_session_manager
from src.storage.models.usage import Usage

from src.logging.logging_config import get_logger

# Set up logging
logger = get_logger(__name__)


class BackgroundTaskService:
    """
    Service for handling background tasks that require independent database sessions.
    This service uses SessionFactory to create services with fresh sessions.
    """

    def __init__(self, context: Context):
        self.context = context

    async def track_model_usage(self, user_id: UUID, model_id: UUID, usage: TokenUsageDTO):
        try:
            async with db_session_manager.session() as session:
                usage_model_repo = BaseRepository(Usage, session)
                usage_service = UsageTrackingService(self.context, usage_model_repo)
                await usage_service.track_usage(user_id, model_id, usage)
        except Exception as e:
            logger.error(
                f"Error tracking model usage for user {user_id}, model {model_id}: {str(e)}",
                exc_info=True,
            )
            self.context.logger.error(traceback.format_exc())
            # Re-raise the exception to ensure FastAPI knows the task failed
            raise e

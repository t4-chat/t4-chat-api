from uuid import UUID
from litellm import Usage

from src.services.usage_tracking_service import UsageTrackingService
from src.services.session_factory import SessionFactory


class BackgroundTaskService:
    """
    Service for handling background tasks that require independent database sessions.
    This service uses SessionFactory to create services with fresh sessions.
    """
    
    def __init__(self):
        pass
        
    def track_model_usage(self, user_id: UUID, model_id: int, usage: Usage):
        with SessionFactory.create_service_with_session(UsageTrackingService) as usage_service:
            usage_service.track_usage(user_id, model_id, usage) 
from typing import Optional
from uuid import UUID


class Context:
    """
    Context object that holds request-specific data like user_id.
    
    By convention, this should be the first parameter in all service constructors:
    def __init__(self, context: Context, other_dependencies...)
    
    This allows services to access the current user's information and other
    request-specific data without having to pass it to every method.
    """
    def __init__(self, user_id: Optional[UUID] = None):
        self.user_id = user_id
        
    @property
    def is_authenticated(self) -> bool:
        """Check if the user is authenticated."""
        return self.user_id is not None

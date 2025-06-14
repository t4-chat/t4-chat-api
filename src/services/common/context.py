from typing import Optional
from uuid import UUID

from fastapi import Depends, Request


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
        return self.user_id is not None


def get_user_id(request: Request) -> Optional[UUID]:
    """Extract user_id from request state."""
    return getattr(request.state, "user_id", None)


def get_context(user_id: Optional[UUID] = Depends(get_user_id)) -> Context:
    """Create and provide a Context instance with user_id from request state."""
    return Context(user_id=user_id)

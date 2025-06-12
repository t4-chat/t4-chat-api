from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.context import Context


class ContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that creates a Context object and overrides the container's context.
    """
    def __init__(self, app, container):
        super().__init__(app)
        self.container = container

    async def dispatch(self, request: Request, call_next):
        # Create a new context with the user_id from auth middleware
        context = Context(user_id=getattr(request.state, "user_id", None))
        
        # Set it in the container
        self.container.context.override(context)
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Reset the override after the request is done
            self.container.context.reset_override() 
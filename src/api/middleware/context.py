from typing import Callable
from fastapi import Request
from src.containers.containers import AppContainer
from src.services.context import Context

def create_context_middleware(container: AppContainer):
    async def middleware(request: Request, call_next: Callable):
        context_instance = Context(user_id=getattr(request.state, "user_id", None))
        with container.context.override(context_instance):
            response = await call_next(request)
        return response
    return middleware
from typing import Callable
from fastapi import Request
from src.services.context import Context, set_context

def create_context_middleware():
    async def middleware(request: Request, call_next: Callable):
        context_instance = Context(user_id=getattr(request.state, "user_id", None))
        set_context(context_instance)
        response = await call_next(request)
        return response
    return middleware
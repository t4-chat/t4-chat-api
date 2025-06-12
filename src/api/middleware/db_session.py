from starlette.requests import Request
from src.storage.db import get_db
from src.storage.db_context import db_session_context

async def db_session_middleware(request: Request, call_next):
    async with get_db() as session:
        token = db_session_context.set(session)
        try:
            response = await call_next(request)
        finally:
            db_session_context.reset(token)
    return response 
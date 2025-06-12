import contextvars
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

db_session_context: contextvars.ContextVar[Optional[AsyncSession]] = contextvars.ContextVar("db_session_context", default=None)


def get_session_from_context() -> AsyncSession:
    session = db_session_context.get()
    if session is None:
        raise RuntimeError("Database session not available in context. " "Ensure DBSessionMiddleware is installed and runs before the request handler.")
    return session

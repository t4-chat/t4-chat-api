from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.config import settings


_engine = None
_SessionLocal = None

def _get_session_maker():
    global _engine, _SessionLocal
    if _SessionLocal is None:
        # Convert URL to async format if needed
        database_url = settings.DATABASE_URL
        if not database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        _engine = create_async_engine(database_url, echo=False, future=True)
        _SessionLocal = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True
        )
    return _SessionLocal

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = _get_session_maker()()
    try:
        yield session
    finally:
        try:
            await session.close()
        except Exception as e:
            print(e)

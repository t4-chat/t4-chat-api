from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.config import settings


class DatabaseSession:
    _instance: Optional["DatabaseSession"] = None
    _engine = None
    _SessionLocal = None

    def __init__(self):
        # Prevent direct instantiation
        if DatabaseSession._instance is not None:
            raise RuntimeError("DatabaseSession is a singleton. Use DatabaseSession.get_instance()")

        # Convert the database URL to async format if it's not already
        self._database_url = settings.DATABASE_URL
        if not self._database_url.startswith("postgresql+asyncpg://"):
            self._database_url = self._database_url.replace("postgresql://", "postgresql+asyncpg://")

    @classmethod
    def get_instance(cls) -> "DatabaseSession":
        if cls._instance is None:
            cls._instance = DatabaseSession()
        return cls._instance

    def _initialize_connection(self):
        if self._engine is None:
            self._engine = create_async_engine(
                self._database_url,
                echo=False,
                future=True
            )
            self._SessionLocal = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )

    @asynccontextmanager
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        if self._SessionLocal is None:
            self._initialize_connection()

        async with self._SessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
            
    async def get_fresh_session(self) -> AsyncSession:
        """
        Create a completely new database session.
        This is useful for background tasks that need to operate
        outside the request lifecycle.
        
        Note: The caller is responsible for closing this session.
        """
        if self._SessionLocal is None:
            self._initialize_connection()
            
        return self._SessionLocal()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with DatabaseSession.get_instance().get_db() as session:
        yield session
        
async def get_fresh_session() -> AsyncSession:
    return await DatabaseSession.get_instance().get_fresh_session()


import os
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class DatabaseSession:
    _instance: Optional["DatabaseSession"] = None
    _engine = None
    _SessionLocal = None

    def __init__(self):
        # Prevent direct instantiation
        if DatabaseSession._instance is not None:
            raise RuntimeError("DatabaseSession is a singleton. Use DatabaseSession.get_instance()")

        self._database_url = os.getenv("DATABASE_URL")

    @classmethod
    def get_instance(cls) -> "DatabaseSession":
        if cls._instance is None:
            cls._instance = DatabaseSession()
        return cls._instance

    def _initialize_connection(self):
        if self._engine is None:
            self._engine = create_engine(self._database_url)
            self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

    @contextmanager
    def get_db(self) -> Generator[Session, None, None]:
        if self._SessionLocal is None:
            self._initialize_connection()

        db = self._SessionLocal()
        try:
            yield db
        finally:
            db.close()


def get_db() -> Generator[Session, None, None]:
    with DatabaseSession.get_instance().get_db() as session:
        yield session

# import logfire
import contextlib

from typing import Annotated
from fastapi import Depends
from typing import Any, AsyncIterator
from sqlalchemy import MetaData

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from src.config import settings

Base = declarative_base()
Base.metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_`%(constraint_name)s`",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

class DatabaseSessionManager():
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        print("Initializing DatabaseSessionManager", flush=True)
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)
        print("DatabaseSessionManager initialized", flush=True)

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    # def instrument_sqlalchemy(self):
    #     logfire.instrument_sqlalchemy(self._engine)

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker(bind=self._engine)
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

class SessionManagerProvider:
    def __init__(self):
        self._session_manager = DatabaseSessionManager(settings.database_url, {"echo": settings.echo_sql})
    
    def get_session_manager(self):
        return self._session_manager
    
    def set_session_manager(self, session_manager: DatabaseSessionManager):
        self._session_manager = session_manager

# Global instance that can be overridden
session_manager_provider = SessionManagerProvider()

async def get_db_session():
    async with session_manager_provider.get_session_manager().session() as session:
        yield session

DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
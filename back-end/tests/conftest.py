import sys
import pytest
import asyncio
import json
import uuid
from typing import AsyncGenerator
from unittest.mock import MagicMock

# Patching sqlalchemy.dialects.postgresql types for SQLite
from sqlalchemy.types import TypeDecorator, TEXT, CHAR, JSON
import sqlalchemy.dialects.postgresql

class SQLiteUUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)

class SQLiteArray(TypeDecorator):
    impl = TEXT
    cache_ok = True
    
    def __init__(self, item_type=None, *args, **kwargs):
        super().__init__()
        self.item_type = item_type

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

# Apply patches
sqlalchemy.dialects.postgresql.UUID = SQLiteUUID
sqlalchemy.dialects.postgresql.JSONB = JSON
sqlalchemy.dialects.postgresql.ARRAY = SQLiteArray

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database.session_manager import Base, get_db_session

# Import all models to ensure they are registered with Base.metadata
from src.modules.agents import models as agent_models
from src.modules.chat import models as chat_models
from src.modules.copilot import models as copilot_models
from src.modules.knowledge_base import models as kb_models
from src.modules.toolsets import models as toolset_models

# Use in-memory SQLite for testing
# check_same_thread=False is needed for sqlite with asyncio
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session
        # Clean up
        await session.rollback()
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    
    app.dependency_overrides.clear()


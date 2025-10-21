# tests/conftest.py
from __future__ import annotations
import os
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy import text
# Test env
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./dignilife_test.db")
os.environ.setdefault("RATE_LIMIT_PER_MIN", "1000")
os.environ.setdefault("ADMIN_KEY", "dev-admin")

# App & DB utils
from src.main import app
from src.db.session import get_session_cm, async_session, Base, engine

@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="session", autouse=True)
async def db_bootstrap() -> AsyncGenerator[None, None]:
    """Create tables once for test run and seed a demo user."""
    # create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # seed data (needs a real CM, not Depends generator)
    async with get_session_cm() as db:
        await db.execute(text(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT
            )
            """
        ))
        await db.execute(text(
            """
            INSERT OR IGNORE INTO users (id, email)
            VALUES ('demo', 'demo@dignilife.ai')
            """
        ))
        await db.commit()
    yield

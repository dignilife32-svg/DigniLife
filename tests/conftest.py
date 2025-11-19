# tests/conftest.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

# ---- App / DB imports (keep these paths same as your project) ----
from src.main import app
from src.db.base import Base  # keep import path if you re-export Base there
from src.db.session import create_tables_once, get_session_ctx
from src.auth.service import require_user
from src.wallet.router import current_user as wallet_current_user

# ---------------------------------------------------------------
# 1) Test environment config (set BEFORE importing app/db elsewhere)
# ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "digi_test.db"
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Force test mode + force sqlite for tests
os.environ.setdefault("TESTING", "1")
os.environ["DATABASE_URL"] = DB_URL

# ---------------------------------------------------------------
# 2) Initialize DB once per test session (create tables + seed)
# ---------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def _init_db() -> None:
    # reset file if exists
    try:
        DB_PATH.unlink()
    except FileNotFoundError:
        pass

    # create all tables (idempotent)
    await create_tables_once()

    # seed a demo user so auth deps work
    async with get_session_ctx() as db:
        await db.execute(
            text("INSERT OR IGNORE INTO users (id, email) VALUES (:id, :email)"),
            {"id": "t0", "email": "demo@dignilife.ai"},
        )
        await db.commit()

    # sanity ping (optional)
    async with get_session_ctx() as db:
        await db.execute(text("SELECT 1"))

# ---------------------------------------------------------------
# 3) Optional: direct DB session fixture for service/logic tests
# ---------------------------------------------------------------
@pytest_asyncio.fixture()
async def db_session():
    async with get_session_ctx() as session:
        yield session

# ---------------------------------------------------------------
# 4) HTTP client fixture (httpx >= 0.28 uses ASGITransport)
# ---------------------------------------------------------------
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
def _override_auth():
    """Skip auth for tests by overriding dependency."""
    from src.auth.security import get_current_user

    app.dependency_overrides[get_current_user] = (
        lambda: {"id": "t0", "role": "admin"}  # pretend admin user
    )
    yield
    app.dependency_overrides.clear()

@pytest_asyncio.fixture()
async def client():
    """Reusable HTTP client for all async tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# FastAPI က sometimes args/kwargs ပေးနိုင်လို့ flexible override လုပ်
async def _fake_user(*args, **kwargs):
    return {"id": "demo"}

# 두 군데 다 override (safety)
app.dependency_overrides[require_user] = _fake_user
app.dependency_overrides[wallet_current_user] = _fake_user

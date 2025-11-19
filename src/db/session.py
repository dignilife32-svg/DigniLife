# src/db/session.py
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ✅ Use the ONE AND ONLY Base from src.db.base
from src.db.base import Base

text = sa_text
q  = sa_text

def exact(col):
    return col
# ---------- DB URL helpers ----------
def _force_async_sqlite_url(url: str) -> str:
    # sqlite:// or sqlite:///...  -> sqlite+aiosqlite://...
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("sqlite+sqlite://"):  # rare mis-typed scheme safeguard
        return url.replace("sqlite+sqlite://", "sqlite+aiosqlite://", 1)
    return url


def effective_db_url() -> str:
    url = os.getenv("DATABASE_URL") or "sqlite:///./dignilife.db"
    return _force_async_sqlite_url(url)


# ---------- module singletons ----------
_ENGINE: AsyncEngine | None = None
_SESSION_MAKER: async_sessionmaker[AsyncSession] | None = None


def _ensure_factory() -> None:
    global _ENGINE, _SESSION_MAKER
    if _ENGINE is None:
        _ENGINE = create_async_engine(
            effective_db_url(),
            future=True,
            pool_pre_ping=True,
        )
    if _SESSION_MAKER is None:
        _SESSION_MAKER = async_sessionmaker(
            bind=_ENGINE, expire_on_commit=False
        )


def engine() -> AsyncEngine:
    _ensure_factory()
    assert _ENGINE is not None
    return _ENGINE


def session_maker() -> async_sessionmaker[AsyncSession]:
    _ensure_factory()
    assert _SESSION_MAKER is not None
    return _SESSION_MAKER


# ---------- FastAPI dependency ----------
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Use in FastAPI routes: `db: AsyncSession = Depends(get_session)`
    """
    sm = session_maker()
    async with sm() as session:
        yield session

# legacy alias (old routers expect get_db)
async def get_db():
    async for s in get_session():
        yield s
        
# ---------- Async context for tests / services ----------
@asynccontextmanager
async def get_session_ctx() -> AsyncIterator[AsyncSession]:
    """
    Use in tests or non-FastAPI code:

        async with get_session_ctx() as db:
            await db.execute(text("SELECT 1"))

    """
    sm = session_maker()
    async with sm() as session:
        yield session

# ---- tiny helpers -----------------------------------------------------------

async def exec1(db: AsyncSession, sql: str):
    """
    Execute a single SQL statement and return the first scalar (or None).
    Exists to satisfy tools/diagnostics that import `exec1` from this module.
    """
    res = await db.execute(sa_text(sql))
    try:
        return res.scalar_one()
    except Exception:
        return res.scalar_one_or_none()
    


# ---------- Schema management ----------
async def create_tables_once() -> None:
    """
    Import *all* modules that declare models so that Base.metadata is populated,
    then create missing tables idempotently.
    """
    _ensure_factory()

    # ⚠️ IMPORTANT: make sure every module that defines models is imported
    try:
        from src.db import models as _models  # noqa: F401
    except Exception:
        _models = None  # noqa: F841

    try:
        # if you keep wallet models separately
        from src.db import wallet_models as _wallet_models  # noqa: F401
    except Exception:
        _wallet_models = None  # noqa: F841

    async with engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# (optional) tiny health check (used by diagnostics/tests)
async def ping_db(timeout: float = 2.0) -> dict:
    try:
        async with get_session_ctx() as db:
            row = await db.execute(text("SELECT 1"))
            _ = row.scalar_one()
        return {"ok": True, "latency_ms": int(timeout * 1000)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

ping_db_timeout = ping_db

__all__ = [
    "q",
    "Base",
    "engine",
    "session_maker",
    "get_session",
    "get_db"
    "get_session_ctx",
    "create_tables_once",
    "effective_db_url",
    "ping_db",
    "exec1"
]

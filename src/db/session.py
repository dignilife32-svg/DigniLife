# src/db/session.py
from __future__ import annotations
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base

# our config (compat: effective_db_url() exists per earlier step)
from src.config import effective_db_url

# ---- single global Base for ALL models ----
Base = declarative_base()

# ---- engine / session factory ----
DB_DSN: str = effective_db_url().replace("sqlite:///", "sqlite+aiosqlite:///")
engine: AsyncEngine = create_async_engine(
    DB_DSN,
    future=True,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as s:
        yield s

# create tables once at startup
async def create_tables_once() -> None:
    # VERY IMPORTANT: import all model modules so metadata knows them
    from src.wallet.models import WalletLedger  # noqa: F401
    # If you have other apps' models, import them here too:
    # from src.db.models import SomeOtherModel  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

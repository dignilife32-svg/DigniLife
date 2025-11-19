# migrations/env.py
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, event
from sqlalchemy.engine import Engine

# ---- Make sure project root is importable (…/.. from this file) ----
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---- Import your app's Base and DB URL resolver ----
from src.db.base import Base                      # single canonical Base
from src.db.session import effective_db_url       # function returning DB URL

# ---- Alembic Config / Logging ----
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# ---- Target metadata for autogenerate ----
target_metadata = Base.metadata


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _get_url() -> str:
    """
    Resolve DB url for Alembic.
    If alembic.ini didn't provide sqlalchemy.url, derive from app function.
    """
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        url = effective_db_url()
        config.set_main_option("sqlalchemy.url", url)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        compare_type=True,            # detect type changes
        literal_binds=True,
        render_as_batch=True,         # IMPORTANT for SQLite ALTER TABLE
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = _get_url()

    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    # Enable SQLite FK checks if needed
    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: N802
        try:
            if _is_sqlite(url):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON;")
                cursor.close()
        except Exception:
            # best-effort only; no crash on older drivers
            pass

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,     # IMPORTANT for SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

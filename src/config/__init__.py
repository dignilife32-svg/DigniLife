# src/config/__init__.py  (compat exports)

from .settings import (
    APP_ENV,
    SQLALCHEMY_DATABASE_URL,   # new primary DSN
    get_db_url,                # new helper
    PROJECT_ROOT,
    REDIS_URL,
)

# ---- Backward-compatible aliases (old names used elsewhere) ----
DB_URL = SQLALCHEMY_DATABASE_URL
DB_SQLITE = SQLALCHEMY_DATABASE_URL if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else ""
effective_db_url = get_db_url

# Some code used STATIC_DIR before; derive from PROJECT_ROOT
from pathlib import Path
STATIC_DIR = (PROJECT_ROOT / "static")  # safe even if folder absent

__all__ = [
    "APP_ENV",
    "DB_URL",
    "DB_SQLITE",
    "SQLALCHEMY_DATABASE_URL",
    "effective_db_url",
    "PROJECT_ROOT",
    "STATIC_DIR",
    "REDIS_URL",
]

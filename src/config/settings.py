# src/config/settings.py
import os
from pathlib import Path

# --- basic app/env ---
APP_ENV = os.getenv("APP_ENV", "dev")

# --- database URLs from .env ---
DB_URL = os.getenv("DB_URL", "").strip()            # e.g. postgres+psycopg://...
DB_SQLITE = os.getenv("DB_SQLITE", "sqlite:///./dignilife.db").strip()

# Alembic / SQLAlchemy both can use this
SQLALCHEMY_DATABASE_URL = DB_URL or DB_SQLITE

def effective_db_url() -> str:
    """Return the DB URL that should be used at runtime."""
    return SQLALCHEMY_DATABASE_URL

# optional: where to mount static files if exists
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = (PROJECT_ROOT / "static")

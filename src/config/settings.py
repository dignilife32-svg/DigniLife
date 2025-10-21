# src/config/settings.py
from __future__ import annotations
import os
from pathlib import Path
from decimal import Decimal

# ------- App / Paths -------
APP_ENV = os.getenv("APP_ENV", "dev").strip()

# project root (for resolving ./dignilife.db on Windows)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = PROJECT_ROOT / "static"  # if you need it elsewhere

# ------- DB URLs from env -------
# Primary (sync for Alembic / tools) or fallback to sqlite file
SQLALCHEMY_DATABASE_URL = (
    os.getenv("DATABASE_URL", "").strip()
    or os.getenv("DB_URL", "").strip()
    or os.getenv("DB_SQLITE", "sqlite:///./dignilife.db").strip()
)

def _sqlite_abspath(url: str, async_driver: bool = False) -> str:
    """
    sqlite:///./file.db  -> sqlite(+aiosqlite):///C:/abs/path/file.db
    Makes Windows-friendly absolute path and switches to aiosqlite for async.
    """
    prefix = "sqlite+aiosqlite:///" if async_driver else "sqlite:///"
    # strip "sqlite:///" or "sqlite+aiosqlite:///"
    raw = url.split(":///")[1] if ":///" in url else url
    abs_path = (PROJECT_ROOT / raw).resolve()
    return prefix + str(abs_path).replace("\\", "/")

def get_db_url(async_driver: bool = False) -> str:
    """
    Read DB URL from env; if sqlite relative path, convert to absolute.
    async_driver=True -> switch sqlite to aiosqlite.
    """
    url = SQLALCHEMY_DATABASE_URL
    if url.startswith("sqlite"):
        return _sqlite_abspath(url, async_driver=async_driver)
    # e.g. postgres://..., leave as-is (for async, user should provide async driver)
    return url

# ------- Redis / Misc (keep what you already had) -------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ------- Bonus defaults (can be overridden per-tenant via DB/env) -------
BONUS_PERCENT      = Decimal(os.getenv("BONUS_PERCENT", "0.05"))   # 5%
BONUS_MIN_CENTS    = Decimal(os.getenv("BONUS_MIN_CENTS", "5"))    # >= $0.05
BONUS_DAILY_CAP_USD= Decimal(os.getenv("BONUS_DAILY_CAP_USD", "3.00"))  # per user/day

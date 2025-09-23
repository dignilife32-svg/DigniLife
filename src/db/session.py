# src/db/session.py
from __future__ import annotations

import os
from typing import Generator, Dict, Any, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# ---- DB URL (env > default sqlite) ----
DB_URL: str = (
    os.getenv("DB_URL")
    or os.getenv("SQLITE", "sqlite:///./dignilife.db")
)

# sqlite အတွက် special arg
connect_args: Dict[str, Any] = (
    {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
)

# ---- Engine / Session factory ----
engine = create_engine(
    DB_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

# Model base export (models.py မှာ Base = declarative_base() မလုပ်တော့)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends() အတွက် DB session provider."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

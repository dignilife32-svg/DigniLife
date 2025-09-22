# src/db/session.py
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = os.getenv("DB_URL") or os.getenv("DB_SQLITE", "sqlite:///./dignilife.db")
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, pool_pre_ping=True, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# src/db/session.py
from sqlite3 import Connection
from typing import Any, Iterable, Optional

def exec(db: Connection, sql: str, params: Iterable[Any] = ()) -> None:
  db.execute(sql, tuple(params))
  db.commit()

def exec1(db: Connection, sql: str, params: Iterable[Any] = ()) -> Optional[tuple]:
  cur = db.execute(sql, tuple(params))
  return cur.fetchone()

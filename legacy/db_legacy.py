# src/db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase

load_dotenv()
DB_URL = os.getenv("DB_URL")

class Base(DeclarativeBase):
    pass

engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

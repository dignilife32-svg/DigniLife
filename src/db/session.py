from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config.settings import SQLALCHEMY_DATABASE_URL, effective_db_url

Base = declarative_base()  # ✅ ADD THIS LINE

# all kwargs must be inside the same parentheses
engine = create_engine(
    SQLALCHEMY_DATABASE_URL or effective_db_url(),
    pool_pre_ping=True,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

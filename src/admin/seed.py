# src/admin/seed.py
from passlib.context import CryptContext
from sqlalchemy import select
from src.db.session import SessionLocal
from src.admin.models import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_admin():
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@local"))
        if not admin:
            u = User(
                email="admin@local",
                phone=None,
                hashed_password=pwd.hash("admin123"),
                is_superuser=True,
                is_active=True,
            )
            db.add(u)
            db.commit()
    finally:
        db.close()

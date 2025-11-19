# src/daily/catalog_seed.py
from sqlalchemy.orm import Session
from src.db import models
from datetime import datetime

# ✅ Base 21 tasks (can expand later)
BASE_TASKS = [
    {"code": "V01", "name": "Voice 3 Words", "category": "voice", "reward_usd": 3.0},
    {"code": "V02", "name": "Pronunciation Check", "category": "voice", "reward_usd": 3.5},
    {"code": "V03", "name": "Story Read & Rate", "category": "voice", "reward_usd": 5.0},
    {"code": "V04", "name": "Translation Snippet", "category": "voice", "reward_usd": 6.0},
    {"code": "G01", "name": "Geo Ping", "category": "geo", "reward_usd": 2.0},
    {"code": "G02", "name": "Local Photo Verify", "category": "geo", "reward_usd": 3.5},
    {"code": "G03", "name": "Environment Check", "category": "geo", "reward_usd": 4.0},
    {"code": "D01", "name": "QR Scan Task", "category": "device", "reward_usd": 3.0},
    {"code": "D02", "name": "App Feedback", "category": "device", "reward_usd": 2.5},
    {"code": "D03", "name": "Screenshot Proof", "category": "device", "reward_usd": 4.0},
    {"code": "S01", "name": "Micro Post", "category": "social", "reward_usd": 2.0},
    {"code": "S02", "name": "Reaction & Rate", "category": "social", "reward_usd": 1.5},
    {"code": "S03", "name": "Mini Survey", "category": "social", "reward_usd": 3.0},
    {"code": "S04", "name": "Friend Invite", "category": "social", "reward_usd": 2.0},
    {"code": "K01", "name": "Fact Check Mini", "category": "data", "reward_usd": 4.0},
    {"code": "K02", "name": "Text Summarize", "category": "data", "reward_usd": 5.0},
    {"code": "K03", "name": "AI Prompt Rating", "category": "data", "reward_usd": 2.5},
    {"code": "SP01", "name": "NGO Survey", "category": "sponsor", "reward_usd": 10.0},
    {"code": "SP02", "name": "Product Feedback", "category": "sponsor", "reward_usd": 7.5},
    {"code": "SP03", "name": "Training Tutorial Watch", "category": "sponsor", "reward_usd": 3.0},
]

def seed_daily_tasks(db: Session):
    """Seed default Daily Earn task catalog (idempotent insert)."""
    for task in BASE_TASKS:
        exists = db.query(models.DailyTask).filter_by(code=task["code"]).first()
        if not exists:
            db.add(models.DailyTask(
                code=task["code"],
                name=task["name"],
                category=task["category"],
                base_reward_usd=task["reward_usd"],
                created_at=datetime.utcnow()
            ))
    db.commit()
    print("✅ Daily Earn base tasks seeded successfully.")

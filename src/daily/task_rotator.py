# src/daily/task_rotator.py
from sqlalchemy.orm import Session
from random import sample
from datetime import datetime, timedelta
from src.db import models

def get_daily_tasks(db: Session, user_id: int, trust_score: float = 1.0, max_tasks: int = 10):
    """Return randomized or tiered daily tasks."""
    all_tasks = db.query(models.DailyTask).all()
    if not all_tasks:
        return []

    # 🎯 Weighted random selection based on trust
    tier_limit = min(max_tasks, len(all_tasks))
    if trust_score < 0.5:
        tier_limit = max(5, tier_limit // 2)

    selected = sample(all_tasks, tier_limit)
    daily_list = []

    for t in selected:
        daily_list.append(models.UserTask(
            user_id=user_id,
            task_code=t.code,
            assigned_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            status="assigned"
        ))

    db.bulk_save_objects(daily_list)
    db.commit()
    return daily_list

def inject_sponsored_tasks(db: Session, user_id: int):
    """Add sponsored tasks dynamically (AI-driven marketing pool)."""
    sponsors = db.query(models.DailyTask).filter(models.DailyTask.category == "sponsor").all()
    if sponsors:
        pick = sample(sponsors, min(2, len(sponsors)))
        for s in pick:
            db.add(models.UserTask(
                user_id=user_id,
                task_code=s.code,
                assigned_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24),
                status="assigned",
                is_sponsored=True
            ))
        db.commit()

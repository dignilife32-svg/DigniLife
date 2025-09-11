# src/daily/controller.py
from datetime import datetime
from .models import TaskSubmission

def submit_daily(submission: TaskSubmission) -> dict:
    ts = submission.submitted_at or datetime.utcnow()
    accuracy = submission.accuracy or 1.0

    base_amount = 1.0
    bonus_multiplier = 1.5 if accuracy >= 0.90 else 1.0
    earned = round(base_amount * bonus_multiplier, 2)

    return {
        "earned": earned,
        "bonus_applied": bonus_multiplier > 1.0,
        "timestamp": ts,
    }

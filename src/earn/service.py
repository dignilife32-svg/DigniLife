# src/earn/service.py
from datetime import datetime
from typing import Literal
from src.daily.models import TaskSubmission
from src.daily.controller import submit_daily
from src.wallet.service import add_to_wallet
from src.earn.models import BonusGrant, BonusPolicy
from src.db import q, exec1

TaskType = Literal["daily", "classic"]

_bonus_policy: BonusPolicy = BonusPolicy()  # in-memory policy

def submit_task(submission: TaskSubmission) -> dict:
    if submission.task_type == "daily":
        result = submit_daily(submission)
    else:
        ts = submission.submitted_at or datetime.utcnow()
        result = {"earned": 2.5, "bonus_applied": False, "timestamp": ts}

    # 1) credit wallet
    new_balance = add_to_wallet(submission.user_id, result["earned"], result["timestamp"])

    # 2) persist task event
    exec1(
        """INSERT INTO tasks(user_id, task_type, accuracy, proof, earned, bonus_applied, submitted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            submission.user_id,
            submission.task_type,
            float(submission.accuracy or 1.0),
            submission.proof,
            float(result["earned"]),
            1 if result["bonus_applied"] else 0,
            result["timestamp"].isoformat(),
        ],
    )

    return {
        "message": "Task submitted successfully.",
        "earned_amount": result["earned"],
        "new_balance": new_balance,
        "bonus_applied": result["bonus_applied"],
        "submitted_at": result["timestamp"],
        "task_type": submission.task_type,
    }

def get_earnings_history(user_id: str, limit: int = 50) -> dict:
    rows = q(
        """SELECT task_type, accuracy, proof, earned, bonus_applied, submitted_at
           FROM tasks WHERE user_id = ? ORDER BY submitted_at DESC LIMIT ?""",
        [user_id, int(limit)],
    )
    total = round(sum(r["earned"] for r in rows), 2)
    # convert ints to bools
    for r in rows:
        r["bonus_applied"] = bool(r["bonus_applied"])
    return {"user_id": user_id, "count": len(rows), "total_earned_in_list": total, "items": rows}

# ----- BONUS ENGINE -----
def get_bonus_policy() -> BonusPolicy:
    return _bonus_policy

def set_bonus_policy(new_policy: BonusPolicy) -> BonusPolicy:
    thr = max(0.0, min(1.0, float(new_policy.accuracy_threshold)))
    mult = max(1.0, float(new_policy.multiplier))
    _bonus_policy.accuracy_threshold = thr
    _bonus_policy.multiplier = mult
    return _bonus_policy

def preview_accuracy_multiplier(accuracy: float) -> float:
    p = get_bonus_policy()
    return p.multiplier if accuracy >= p.accuracy_threshold else 1.0

def grant_manual_bonus(payload: BonusGrant) -> dict:
    ts = datetime.utcnow()
    new_balance = add_to_wallet(payload.user_id, round(payload.amount, 2), ts)
    exec1("INSERT INTO bonuses(user_id, amount, reason, granted_at) VALUES (?, ?, ?, ?)",
          [payload.user_id, float(payload.amount), payload.reason or "manual", ts.isoformat()])
    # mirror in tasks? not necessary; history stays in its own table; admin views read both.
    return {
        "message": "Bonus granted.",
        "bonus_amount": round(payload.amount, 2),
        "new_balance": new_balance,
        "reason": payload.reason or "manual",
        "submitted_at": ts
    }

def get_task_stats() -> dict:
    count = q("SELECT COUNT(*) c FROM tasks")[0]["c"]
    users = q("SELECT COUNT(DISTINCT user_id) c FROM tasks")[0]["c"]
    total = q("SELECT ROUND(COALESCE(SUM(earned),0),2) s FROM tasks")[0]["s"]
    recent = q("""SELECT user_id, task_type, earned, bonus_applied, submitted_at
                  FROM tasks ORDER BY submitted_at DESC LIMIT 5""")
    for r in recent: r["bonus_applied"] = bool(r["bonus_applied"])
    return {
        "users_with_activity": users,
        "total_task_events": count,
        "total_earned": total,
        "recent": recent
    }

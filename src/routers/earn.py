# src/routers/earn.py
from __future__ import annotations

from datetime import timedelta
from uuid import uuid4
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.db.session import get_db
from src.auth import get_current_user
from src.ai.auto_check import quality_check
from src.services.wallet_tx import post_earn_credit

router = APIRouter(prefix="/earn", tags=["earn"])

# -----------------------------
# Payout & safety configuration
# -----------------------------
HOURLY_CAP_DEFAULT: float = 300.0
DAILY_CAP_DEFAULT: float = 500.0
BASE_REWARD_DAILY: float = 3.0
BASE_REWARD_CLASSIC: float = 5.0
ASSIGNMENT_TTL_MINUTES: int = 10  # how long an assignment is valid


# -----------------------------
# Helper queries (SQLite safe)
# -----------------------------
def _sum_reward_last_hour(db: Session, user_id: str) -> float:
    val = db.execute(
        text(
            """
            SELECT COALESCE(SUM(reward_usd), 0.0)
            FROM submissions
            WHERE user_id = :uid
              AND created_at >= datetime('now','-1 hour')
            """
        ),
        {"uid": user_id},
    ).scalar()
    return float(val or 0.0)


def _sum_reward_today(db: Session, user_id: str) -> float:
    val = db.execute(
        text(
            """
            SELECT COALESCE(SUM(reward_usd), 0.0)
            FROM submissions
            WHERE user_id = :uid
              AND date(created_at) = date('now')
            """
        ),
        {"uid": user_id},
    ).scalar()
    return float(val or 0.0)


def assignment_valid(db: Session, assignment_id: str, user_id: str) -> bool:
    """
    issued to this user, not expired, not already submitted
    """
    val = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM assignments a
            LEFT JOIN submissions s ON s.assignment_id = a.id
            WHERE a.id = :aid
              AND a.user_id = :uid
              AND a.status = 'issued'
              AND a.expires_at > datetime('now')
              AND s.id IS NULL
            """
        ),
        {"aid": assignment_id, "uid": user_id},
    ).scalar()
    return bool(int(val or 0))


# -----------------------------
# Task picking (daily/classic)
# -----------------------------
def _pick_task(db: Session, kind: str) -> Dict[str, Any] | None:
    """
    Pick a single available task of given kind.
    Assumes a `tasks` table with (id, kind, payload, created_at, expires_at).
    """
    row = (
        db.execute(
            text(
                """
                SELECT id, payload
                FROM tasks
                WHERE kind = :kind
                  AND (expires_at IS NULL OR expires_at > datetime('now'))
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"kind": kind},
        )
        .mappings()
        .fetchone()
    )
    return dict(row) if row else None


def _issue_assignment(
    db: Session,
    task_id: str,
    user_id: str,
    base_reward: float,
) -> str:
    aid = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO assignments
                (id, task_id, user_id, status, issued_at, expires_at, reward_base)
            VALUES
                (:aid, :tid, :uid, 'issued', datetime('now'),
                 datetime('now', :ttl), :base)
            """
        ),
        {
            "aid": aid,
            "tid": task_id,
            "uid": user_id,
            "ttl": f"+{ASSIGNMENT_TTL_MINUTES} minutes",
            "base": base_reward,
        },
    )
    db.commit()
    return aid


# -----------------------------
# Next (get assignment)
# -----------------------------
@router.get("/daily/next")
def daily_next(db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = _pick_task(db, "daily")
    if not task:
        return {"empty": True}
    aid = _issue_assignment(db, task_id=task["id"], user_id=user.id, base_reward=BASE_REWARD_DAILY)
    return {"assignment_id": aid, "payload": task["payload"]}


@router.get("/classic/next")
def classic_next(db: Session = Depends(get_db), user=Depends(get_current_user)):
    task = _pick_task(db, "classic")
    if not task:
        return {"empty": True}
    aid = _issue_assignment(db, task_id=task["id"], user_id=user.id, base_reward=BASE_REWARD_CLASSIC)
    return {"assignment_id": aid, "payload": task["payload"]}


# -----------------------------
# Submit (with AI quality check)
# -----------------------------
def _cap_adjusted_reward(db: Session, user_id: str, proposed: float) -> float:
    """
    Respect hourly & daily caps by trimming proposed reward if needed.
    """
    hour_used = _sum_reward_last_hour(db, user_id)
    day_used = _sum_reward_today(db, user_id)

    if hour_used >= HOURLY_CAP_DEFAULT and day_used >= DAILY_CAP_DEFAULT:
        return 0.0

    # remaining headroom
    hour_left = max(HOURLY_CAP_DEFAULT - hour_used, 0.0)
    day_left = max(DAILY_CAP_DEFAULT - day_used, 0.0)
    allowed = min(hour_left, day_left) if day_left < hour_left else hour_left
    # if daily is tighter, use daily; otherwise hourly
    allowed = min(allowed, day_left)
    return max(0.0, min(proposed, allowed))


@router.post("/daily/submit")
def daily_submit(
    assignment_id: str = Body(..., embed=True),
    payload: Dict[str, Any] = Body(..., embed=True),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not assignment_valid(db, assignment_id, user.id):
        raise HTTPException(status_code=400, detail="invalid / expired / duplicate")

    ok, reason, confidence = quality_check(payload)

    base = BASE_REWARD_DAILY
    reward = _cap_adjusted_reward(db, user.id, base)
    needs_review = not ok or reward <= 0.0

    sid = str(uuid4())
    # record submission
    db.execute(
        text(
            """
            INSERT INTO submissions
                (id, assignment_id, user_id, reward_usd, reason, needs_review, created_at)
            VALUES
                (:sid, :aid, :uid, :reward, :reason, :needs, datetime('now'))
            """
        ),
        {
            "sid": sid,
            "aid": assignment_id,
            "uid": user.id,
            "reward": reward,
            "reason": reason if reason else "ok",
            "needs": 1 if needs_review else 0,
        },
    )
    db.execute(text("UPDATE assignments SET status='submitted' WHERE id=:aid"), {"aid": assignment_id})
    db.commit()

    # credit wallet (single TX)
    post_earn_credit(
        db=db,
        user_id=user.id,
        amount_usd=reward,
        ref_type="submission",
        ref_id=sid,
        meta={"confidence": confidence, "needs_review": needs_review, "kind": "daily"},
    )

    return {"ok": True, "reward_usd": reward, "reason": reason, "confidence": confidence}


@router.post("/classic/submit")
def classic_submit(
    assignment_id: str = Body(..., embed=True),
    payload: Dict[str, Any] = Body(..., embed=True),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not assignment_valid(db, assignment_id, user.id):
        raise HTTPException(status_code=400, detail="invalid / expired / duplicate")

    ok, reason, confidence = quality_check(payload)

    base = BASE_REWARD_CLASSIC
    reward = _cap_adjusted_reward(db, user.id, base)
    needs_review = not ok or reward <= 0.0

    sid = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO submissions
                (id, assignment_id, user_id, reward_usd, reason, needs_review, created_at)
            VALUES
                (:sid, :aid, :uid, :reward, :reason, :needs, datetime('now'))
            """
        ),
        {
            "sid": sid,
            "aid": assignment_id,
            "uid": user.id,
            "reward": reward,
            "reason": reason if reason else "ok",
            "needs": 1 if needs_review else 0,
        },
    )
    db.execute(text("UPDATE assignments SET status='submitted' WHERE id=:aid"), {"aid": assignment_id})
    db.commit()

    post_earn_credit(
        db=db,
        user_id=user.id,
        amount_usd=reward,
        ref_type="submission",
        ref_id=sid,
        meta={"confidence": confidence, "needs_review": needs_review, "kind": "classic"},
    )

    return {"ok": True, "reward_usd": reward, "reason": reason, "confidence": confidence}

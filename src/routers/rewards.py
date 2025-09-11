# src/routers/rewards.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import secrets
import string
from typing import List, Dict, Any

# local imports (keep these paths the same as your project)
from src.db.session import get_db
from src.db.models import Reward, Referral
from src.utils.auth import get_current_user  # stub or your real auth

router = APIRouter(prefix="/rewards", tags=["rewards"])


# ---------- helpers ----------
def _random_code(n: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def _gen_unique_code(db: Session, n: int = 8) -> str:
    """Generate a code that doesn't collide with existing Referral.code."""
    # small loop; collision chance is tiny with 36^8, but we still check.
    for _ in range(10):
        code = _random_code(n)
        exists = db.query(Referral).filter(Referral.code == code).first()
        if not exists:
            return code
    # extremely unlikely
    raise HTTPException(500, "Could not generate unique referral code")


# ---------- routes ----------
@router.post("/referral/create_code")
def create_referral_code(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    """
    Create a new referral code for the current user (inviter).
    Returns: {"code": "ABCD1234"}
    """
    code = _gen_unique_code(db)

    ref = Referral(
        inviter_user_id=user.id,
        code=code,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)

    return {"code": code, "referral_id": ref.id}


@router.post("/referral/use")
def use_referral(
    code: str = Query(..., min_length=4, description="Referral code to redeem"),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    """
    Use (redeem) a referral code as the invitee.
    Awards points to the inviter and marks the referral as completed.
    """
    ref = db.query(Referral).filter(Referral.code == code).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Invalid referral code")

    if ref.inviter_user_id == getattr(user, "id", None):
        raise HTTPException(status_code=400, detail="You cannot use your own code")

    if ref.invitee_user_id:
        raise HTTPException(status_code=400, detail="Code has already been used")

    # mark referral completed
    ref.invitee_user_id = user.id
    ref.status = "completed"
    ref.completed_at = datetime.utcnow()

    # award points to inviter (tweak points as you like)
    award_points = 100
    reward = Reward(
        user_id=ref.inviter_user_id,
        points=award_points,
        reason="referral_signup",
        created_at=datetime.utcnow(),
    )
    db.add(reward)
    db.commit()

    return {
        "ok": True,
        "inviter_id": ref.inviter_user_id,
        "invitee_id": user.id,
        "awarded_points": award_points,
    }


@router.get("/me")
def my_rewards(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    """
    Get current user's rewards summary and list.
    """
    total_points = (
        db.query(func.coalesce(func.sum(Reward.points), 0))
        .filter(Reward.user_id == user.id)
        .scalar()
        or 0
    )
    items: List[Dict[str, Any]] = [
        {
            "id": r.id,
            "points": r.points,
            "reason": r.reason,
            "created_at": r.created_at,
        }
        for r in db.query(Reward).filter(Reward.user_id == user.id).order_by(Reward.id.desc()).all()
    ]
    return {"user_id": user.id, "total_points": total_points, "rewards": items}


@router.get("/referral/my-codes")
def my_referral_codes(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    """
    List my generated referral codes and statuses.
    """
    codes = (
        db.query(Referral)
        .filter(Referral.inviter_user_id == user.id)
        .order_by(Referral.id.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "code": r.code,
            "status": r.status,
            "created_at": r.created_at,
            "completed_at": r.completed_at,
            "invitee_user_id": r.invitee_user_id,
        }
        for r in codes
    ]

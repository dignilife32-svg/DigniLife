# src/earn/router.py
from fastapi import APIRouter, Query, Depends
from src.auth.security import require_admin
from src.audit.service import log_admin_action
from src.daily.models import TaskSubmission
from fastapi import HTTPException
from src.ratelimit import check_rate, RateLimitExceeded
from src.earn.models import BonusGrant, BonusPolicy
from .service import (
    submit_task, get_earnings_history,
    get_bonus_policy, set_bonus_policy, grant_manual_bonus
)

router = APIRouter(prefix="/task", tags=["task"])

@router.post("/submit")
def task_submit(submission: TaskSubmission):
    return submit_task(submission)

@router.get("/earnings/history")
def earnings_history(user_id: str = Query(..., min_length=1), limit: int = 50):
    return get_earnings_history(user_id=user_id, limit=limit)

# ----- BONUS ENDPOINTS -----
@router.get("/bonus/policy")
def bonus_policy_get() -> BonusPolicy:
    return get_bonus_policy()

# ⚠️ MVP: no auth yet. Later: protect with admin auth.
@router.post("/bonus/policy")
def bonus_policy_set(payload: BonusPolicy) -> BonusPolicy:
    return set_bonus_policy(payload)

@router.post("/bonus/grant")
def bonus_grant(payload: BonusGrant):
    return grant_manual_bonus(payload)

# ...
@router.post("/bonus/policy", dependencies=[Depends(require_admin)])
def bonus_policy_set(payload: BonusPolicy) -> BonusPolicy:
    return set_bonus_policy(payload)

@router.post("/bonus/grant", dependencies=[Depends(require_admin)])
def bonus_grant(payload: BonusGrant):
    return grant_manual_bonus(payload)

# existing @router.post("/bonus/policy", ...) stays protected
@router.post("/bonus/policy", dependencies=[Depends(require_admin)])
def bonus_policy_set(payload: BonusPolicy, admin=Depends(require_admin)) -> BonusPolicy:
    updated = set_bonus_policy(payload)
    # audit
    log_admin_action(admin_id=admin["sub"], action="bonus.policy.set", payload=payload.dict())
    return updated

@router.post("/bonus/grant", dependencies=[Depends(require_admin)])
def bonus_grant(payload: BonusGrant, admin=Depends(require_admin)):
    res = grant_manual_bonus(payload)
    log_admin_action(admin_id=admin["sub"], action="bonus.grant",
                     payload={"user_id": payload.user_id, "amount": payload.amount, "reason": payload.reason},
                     target_user=payload.user_id)
    return res

@router.post("/submit")
def task_submit(submission: TaskSubmission):
    try:
        # user_id required in TaskSubmission; rate: 30 req / 60s / user
        check_rate(key=f"task:{submission.user_id}", limit=30, window_sec=60)
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    return submit_task(submission)

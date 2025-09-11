# src/wallet/router.py
from fastapi import APIRouter, Query, Depends, HTTPException
from src.audit.service import log_admin_action
from src.auth.security import require_admin, require_user
from fastapi import HTTPException
from src.ratelimit import check_rate, RateLimitExceeded
from src.wallet.service import get_wallet_summary
# ⬇️ ADD:
from src.wallet.models import WithdrawRequestBody, WithdrawAdminAction
from src.wallet.service import (
    request_withdraw, get_user_withdrawals,
    admin_list_withdrawals, approve_withdraw, reject_withdraw
)
from src.auth.security import require_user, require_admin

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.get("/summary")
def wallet_summary(user_id: str = Query(..., min_length=1)):
    return get_wallet_summary(user_id)

# ⬇️ USER endpoints (require token but any role ok)
@router.post("/withdraw/request", dependencies=[Depends(require_user)])
def withdraw_request(body: WithdrawRequestBody, user=Depends(require_user)):
    try:
        return request_withdraw(user_id=user["sub"], amount=body.amount, method=body.method, details=body.details)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/withdraw/list", dependencies=[Depends(require_user)])
def withdraw_list(limit: int = 50, user=Depends(require_user)):
    return get_user_withdrawals(user_id=user["sub"], limit=limit)

# ⬇️ ADMIN endpoints
@router.get("/withdraw/requests", dependencies=[Depends(require_admin)])
def admin_withdraw_requests(status: str | None = None, limit: int = 100):
    return admin_list_withdrawals(status=status, limit=limit)

@router.post("/withdraw/approve", dependencies=[Depends(require_admin)])
def admin_withdraw_approve(body: WithdrawAdminAction):
    try:
        return approve_withdraw(withdraw_id=body.withdraw_id, tx_ref=body.tx_ref)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/withdraw/reject", dependencies=[Depends(require_admin)])
def admin_withdraw_reject(body: WithdrawAdminAction):
    try:
        return reject_withdraw(withdraw_id=body.withdraw_id, tx_ref=body.tx_ref)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/withdraw/approve", dependencies=[Depends(require_admin)])
def admin_withdraw_approve(body: WithdrawAdminAction, admin=Depends(require_admin)):
    try:
        res = approve_withdraw(withdraw_id=body.withdraw_id, tx_ref=body.tx_ref)
        log_admin_action(admin_id=admin["sub"], action="withdraw.approve",
                         payload={"withdraw_id": body.withdraw_id, "tx_ref": body.tx_ref})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/withdraw/reject", dependencies=[Depends(require_admin)])
def admin_withdraw_reject(body: WithdrawAdminAction, admin=Depends(require_admin)):
    try:
        res = reject_withdraw(withdraw_id=body.withdraw_id, tx_ref=body.tx_ref)
        log_admin_action(admin_id=admin["sub"], action="withdraw.reject",
                         payload={"withdraw_id": body.withdraw_id, "tx_ref": body.tx_ref})
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/withdraw/request", dependencies=[Depends(require_user)])
def withdraw_request(body: WithdrawRequestBody, user=Depends(require_user)):
    try:
        check_rate(key=f"withdraw:{user['sub']}", limit=5, window_sec=3600)  # 5/hour
        return request_withdraw(user_id=user["sub"], amount=body.amount, method=body.method, details=body.details)
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

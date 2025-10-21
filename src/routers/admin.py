# src/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import Optional
from src.admin.queue import list_withdrawals, approve, reject
from src.security import require_admin  # your existing guard

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/withdraw/queue")
def admin_queue_list(
    status_filter: str = Query("pending"),
    _=Depends(require_admin),
):
    return {"items": list_withdrawals(status_filter)}

@router.post("/withdraw/{wid}/approve")
def admin_withdraw_approve(
    wid: str, note: Optional[str] = Body(default=""), _=Depends(require_admin)
):
    try:
        return approve(wid, note=note or "")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/withdraw/{wid}/reject")
def admin_withdraw_reject(
    wid: str, reason: Optional[str] = Body(default="not_specified"), _=Depends(require_admin)
):
    try:
        return reject(wid, reason=reason or "not_specified")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

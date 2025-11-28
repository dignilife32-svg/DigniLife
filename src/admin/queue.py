# src/admin/queue.py
from typing import List, Dict
from sqlalchemy.orm import Session
from src.db.models import WithdrawRequest, WalletTxn
from src.db.session import get_session_ctx
from sqlalchemy import update

def list_withdrawals(db: Session, status: str = "pending") -> List[Dict]:
    q = db.query(WithdrawRequest).filter(WithdrawRequest.status == status).order_by(WithdrawRequest.created_at.asc())
    return [{
        "id": w.id, "user_id": w.user_id, "amount_usd": round((w.amount or 0)/100, 2),
        "status": w.status, "reason": w.reason,
        "dst_kind": (w.destination_info or {}).get("dst_kind"),
        "dst_account": (w.destination_info or {}).get("dst_account"),
        "created_at": w.created_at.isoformat(),
        "updated_at": w.updated_at.isoformat() if w.updated_at else None,
    } for w in q.all()]

async def approve(withdraw_id: str, admin_id: str):
    async with get_session_ctx() as db:
        q = (
            update(WithdrawRequest)
            .where(WithdrawRequest.id == withdraw_id)
            .values(status="approved", admin_id=admin_id)
        )
        await db.execute(q)
        await db.commit()
    return {"ok": True, "id": withdraw_id, "status": "approved"}

async def reject(withdraw_id: str, admin_id: str, reason: str = ""):
    async with get_session_ctx() as db:
        q = (
            update(WithdrawRequest)
            .where(WithdrawRequest.id == withdraw_id)
            .values(status="rejected", admin_id=admin_id, admin_note=reason)
        )
        await db.execute(q)
        await db.commit()
    return {
        "ok": True,
        "id": withdraw_id,
        "status": "rejected",
        "reason": reason,
    }

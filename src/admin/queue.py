# src/admin/queue.py
from typing import List, Dict
from sqlalchemy.orm import Session
from src.db.models import WithdrawRequest, WalletTxn

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

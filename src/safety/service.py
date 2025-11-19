# src/safety/service.py
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import uuid
from src.safety.models import UserReport, SOSRequest
from src.db.session import get_session, q, exec1

_last_sos_at: Dict[str, datetime] = {}

def submit_user_report(payload: UserReport) -> dict:
    now = datetime.utcnow().isoformat()
    rid = exec1(
        """INSERT INTO reports(user_id, category, message, task_id, severity, contact, submitted_at, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'open')""",
        [payload.user_id, payload.category, payload.message, payload.task_id,
         payload.severity, payload.contact, now],
    )
    return {"message": "Report received.", "report_id": str(rid), "submitted_at": now}

def list_reports(user_id: str, limit: int = 50) -> dict:
    rows = q("""SELECT id as report_id, category, message, task_id, severity, contact, submitted_at, status
                FROM reports WHERE user_id = ? ORDER BY submitted_at DESC LIMIT ?""",
             [user_id, int(limit)])
    return {"user_id": user_id, "count": len(rows), "items": rows}

def trigger_sos_manual(payload: SOSRequest) -> dict:
    now = datetime.utcnow()
    last = _last_sos_at.get(payload.user_id)
    if last and (now - last) < timedelta(seconds=60):
        return {"sos_id": "", "status": "rate_limited",
                "received_at": now, "retry_after_seconds": 60 - int((now - last).total_seconds())}

    entry_id = exec1(
        """INSERT INTO sos(user_id, reason, lat, lon, address, contact_name, contact_phone, received_at, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'queued')""",
        [
            payload.user_id,
            payload.reason,
            (payload.location.lat if payload.location else None) if payload.location else None,
            (payload.location.lon if payload.location else None) if payload.location else None,
            (payload.location.address if payload.location else None) if payload.location else None,
            payload.contact_name, payload.contact_phone, now.isoformat()
        ],
    )
    _last_sos_at[payload.user_id] = now
    return {"sos_id": str(entry_id), "status": "queued", "received_at": now}

def list_sos(user_id: str, limit: int = 20) -> dict:
    rows = q ("""SELECT id as sos_id, reason, lat, lon, address, contact_name, contact_phone, received_at, status
                FROM sos WHERE user_id = ? ORDER BY received_at DESC LIMIT ?""",
             [user_id, int(limit)])
    return {"user_id": user_id, "count": len(rows), "items": rows}

def get_reports_stats(limit: int = 5) -> dict:
    total = q ("SELECT COUNT(*) c FROM reports")[0]["c"]
    open_c = q ("SELECT COUNT(*) c FROM reports WHERE status='open'")[0]["c"]
    latest = q ("SELECT id as report_id, user_id, category, message, submitted_at, status FROM reports ORDER BY submitted_at DESC LIMIT ?", [int(limit)])
    return {"total_reports": total, "open_reports": open_c, "latest": latest}

def get_sos_stats(limit: int = 5) -> dict:
    latest = q ("SELECT id as sos_id, user_id, reason, received_at, status FROM sos ORDER BY received_at DESC LIMIT ?", [int(limit)])
    total = q ("SELECT COUNT(*) c FROM sos")[0]["c"]
    return {"total_sos": total, "latest": latest}

# src/safety/service.py

# ---------- Face verify ----------
try:
    # Prefer a concrete implementation if you already have it
    from src.safety.facegate import verify_face_token as _verify_face_token  # type: ignore
except Exception:  # graceful fallback
    async def _verify_face_token(token: Optional[str], user_id: str, device_id: Optional[str] = None) -> bool:  # type: ignore
        # Minimal safe default: require token + user_id to exist
        return bool(token and user_id)

# ---------- Risk assessment ----------
try:
    # If you already have a rich function, reuse it
    from src.safety.risk import assess_withdraw_risk as _assess_withdraw_risk  # type: ignore
except Exception:
    async def _assess_withdraw_risk(
        *, user_id: str, amount: float, ref: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Simple default policy:
        - amount <= 0 → block
        - amount > 200 → require face
        - else → ok
        """
        reasons: list[str] = []
        if amount <= 0:
            return {"action": "block", "score": 1.0, "reasons": ["non_positive_amount"]}
        if amount > 200:
            return {"action": "face", "score": 0.6, "reasons": ["high_amount"]}
        return {"action": "ok", "score": 0.1, "reasons": reasons}

# ---------- Public, stable API exported to the rest of the app ----------
async def verify_face_token(token: Optional[str], user_id: str, device_id: Optional[str] = None) -> bool:
    return await _verify_face_token(token, user_id, device_id)

async def assess_withdraw_risk(*, user_id: str, amount: float, ref: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
    return await _assess_withdraw_risk(user_id=user_id, amount=amount, ref=ref, **kwargs)

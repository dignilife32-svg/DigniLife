# src/audit/service.py
import json
from typing import Optional, Dict, Any, List
from src.utils.db_helpers import exec, exec1, q

def log_admin_action(admin_id: str, action: str, payload: Dict[str, Any], target_user: Optional[str] = None) -> int:
    return exec1(
        "INSERT INTO admin_audit(admin_id, action, target_user, payload) VALUES (?, ?, ?, ?)",
        [admin_id, action, target_user, json.dumps(payload, ensure_ascii=False)],
    )

def list_admin_audit(limit: int = 100) -> Dict[str, Any]:
    rows = q("""SELECT id, admin_id, action, target_user, payload, created_at
                FROM admin_audit ORDER BY id DESC LIMIT ?""", [int(limit)])
    return {"count": len(rows), "items": rows}

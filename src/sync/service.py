# src/sync/service.py
import json
from datetime import datetime
from typing import List, Dict

from src.db import q, exec1, q
from src.sync.models import SyncOp, SyncPushResult
from src.earn.service import submit_task, grant_manual_bonus
from src.earn.models import BonusGrant
from src.daily.models import TaskSubmission
from src.safety.service import submit_user_report, trigger_sos_manual
from src.safety.models import UserReport, SOSRequest, Geo

def _record_received(op: SyncOp):
    try:
        exec1(
            """INSERT INTO sync_ops(client_op_id, user_id, op_type, payload_json, status)
               VALUES (?, ?, ?, ?, 'received')""",
            [op.op_id, op.user_id, op.op_type, json.dumps(op.payload, ensure_ascii=False)],
        )
        return True
    except Exception:
        # likely UNIQUE conflict => already seen
        return False

def _mark_applied(op_id: str, result: dict):
    exec1("""UPDATE sync_ops SET status='applied', result_json=?, applied_at=? WHERE client_op_id=?""",
          [json.dumps(result, default=str), datetime.utcnow().isoformat(), op_id])

def _mark_failed(op_id: str, error: str):
    exec1("""UPDATE sync_ops SET status='failed', error=?, applied_at=? WHERE client_op_id=?""",
          [error, datetime.utcnow().isoformat(), op_id])

def process_ops(ops: List[SyncOp]) -> List[SyncPushResult]:
    results: List[SyncPushResult] = []

    for op in ops:
        # idempotency: if exists and applied -> return duplicate with stored result
        row = q("SELECT status, result_json, error FROM sync_ops WHERE client_op_id=?", [op.op_id])
        if row and row[0]["status"] == "applied":
            results.append(SyncPushResult(op_id=op.op_id, status="duplicate",
                                          result=json.loads(row[0]["result_json"]) if row[0]["result_json"] else None))
            continue
        if not row:
            _record_received(op)

        try:
            if op.op_type == "task.submit":
                result = submit_task(TaskSubmission(**op.payload))
            elif op.op_type == "bonus.grant":
                result = grant_manual_bonus(BonusGrant(**op.payload))
            elif op.op_type == "user.report":
                result = submit_user_report(UserReport(**op.payload))
            elif op.op_type == "sos.manual":
                # payload.location is dict; Pydantic will coerce
                result = trigger_sos_manual(SOSRequest(**op.payload))
            else:
                raise ValueError(f"Unknown op_type: {op.op_type}")

            _mark_applied(op.op_id, result)
            results.append(SyncPushResult(op_id=op.op_id, status="applied", result=result))
        except Exception as e:
            _mark_failed(op.op_id, str(e))
            results.append(SyncPushResult(op_id=op.op_id, status="failed", error=str(e)))

    return results

def pull_since(user_id: str, since_iso: str | None) -> Dict:
    # Return server-side changes for the user since timestamp (inclusive)
    params = [user_id]
    where = "WHERE user_id = ?"
    if since_iso:
        where += " AND submitted_at >= ?"
        params.append(since_iso)

    tasks = q(f"""SELECT id, task_type, accuracy, proof, earned, bonus_applied, submitted_at
                  FROM tasks {where} ORDER BY submitted_at ASC""", params)

    bonuses = q(
        f"""SELECT id, amount, reason, granted_at
            FROM bonuses WHERE user_id = ? {"AND granted_at >= ?" if since_iso else ""} ORDER BY granted_at ASC""",
        params
    )

    reports = q(
        f"""SELECT id, category, message, severity, submitted_at, status
            FROM reports WHERE user_id = ? {"AND submitted_at >= ?" if since_iso else ""} ORDER BY submitted_at ASC""",
        params
    )

    sos = q(
        f"""SELECT id, reason, lat, lon, address, contact_name, contact_phone, received_at, status
            FROM sos WHERE user_id = ? {"AND received_at >= ?" if since_iso else ""} ORDER BY received_at ASC""",
        params
    )

    # normalize types
    for t in tasks: t["bonus_applied"] = bool(t["bonus_applied"])

    return {
        "since": since_iso,
        "tasks": tasks,
        "bonuses": bonuses,
        "reports": reports,
        "sos": sos
    }

# src/wallet/service.py
from datetime import datetime
from src.db import q, exec1
from typing import List, Dict
def _ensure_wallet(user_id: str):
    rows = q("SELECT user_id FROM wallets WHERE user_id = ?", [user_id])
    if not rows:
        exec1("INSERT INTO wallets(user_id, available_balance, pending_withdrawal) VALUES (?, 0, 0)", [user_id])

def add_to_wallet(user_id: str, amount: float, ts: datetime) -> float:
    _ensure_wallet(user_id)
    exec1(
        "UPDATE wallets SET available_balance = ROUND(available_balance + ?, 2), last_contribution = ? WHERE user_id = ?",
        [float(amount), ts.isoformat(), user_id],
    )
    return get_wallet(user_id)["available_balance"]

def get_wallet(user_id: str) -> dict:
    _ensure_wallet(user_id)
    row = q("SELECT user_id, available_balance, pending_withdrawal, last_contribution FROM wallets WHERE user_id = ?", [user_id])[0]
    return row

def get_wallet_summary(user_id: str) -> dict:
    w = get_wallet(user_id)
    return {
        "user_id": user_id,
        "available_balance": w["available_balance"],
        "pending_withdrawal": w["pending_withdrawal"],
        "last_contribution": w["last_contribution"],
    }

def get_all_wallets_summary() -> dict:
    rows = q("SELECT user_id, available_balance, pending_withdrawal, last_contribution FROM wallets")
    total = sum(r["available_balance"] for r in rows)
    top = sorted(rows, key=lambda r: r["available_balance"], reverse=True)[:5]
    return {
        "wallet_users": len(rows),
        "total_available_balance": round(total, 2),
        "top_balances": top
    }

MIN_WITHDRAW = 0.50  # prevent tiny spam payouts

def _ensure_wallet(user_id: str):
    rows = q("SELECT user_id FROM wallets WHERE user_id = ?", [user_id])
    if not rows:
        exec1("INSERT INTO wallets(user_id, available_balance, pending_withdrawal) VALUES (?, 0, 0)", [user_id])

def request_withdraw(user_id: str, amount: float, method: str, details: str | None) -> dict:
    _ensure_wallet(user_id)
    if amount < MIN_WITHDRAW:
        raise ValueError(f"Minimum withdraw is {MIN_WITHDRAW:.2f}")
    w = q("SELECT available_balance, pending_withdrawal FROM wallets WHERE user_id=?", [user_id])[0]
    if float(w["available_balance"]) < amount:
        raise ValueError("Insufficient available balance")

    # move funds: available -> pending
    ts = datetime.utcnow().isoformat()
    exec1("UPDATE wallets SET available_balance = ROUND(available_balance - ?,2), "
          "pending_withdrawal = ROUND(pending_withdrawal + ?,2) WHERE user_id = ?",
          [amount, amount, user_id])

    wid = exec1(
        "INSERT INTO withdrawals(user_id, amount, method, details, status, requested_at) "
        "VALUES (?, ?, ?, ?, 'requested', ?)",
        [user_id, amount, method, details, ts]
    )
    return {"withdraw_id": wid, "status": "requested", "requested_at": ts, "amount": round(amount,2)}

def get_user_withdrawals(user_id: str, limit: int = 50) -> dict:
    rows = q("SELECT id as withdraw_id, amount, method, details, status, requested_at, decided_at, tx_ref "
             "FROM withdrawals WHERE user_id=? ORDER BY requested_at DESC LIMIT ?", [user_id, int(limit)])
    return {"user_id": user_id, "count": len(rows), "items": rows}

def admin_list_withdrawals(status: str | None = None, limit: int = 100) -> dict:
    if status:
        rows = q("SELECT id as withdraw_id, user_id, amount, method, status, requested_at "
                 "FROM withdrawals WHERE status=? ORDER BY requested_at ASC LIMIT ?", [status, int(limit)])
    else:
        rows = q("SELECT id as withdraw_id, user_id, amount, method, status, requested_at "
                 "FROM withdrawals ORDER BY requested_at ASC LIMIT ?", [int(limit)])
    return {"count": len(rows), "items": rows}

def approve_withdraw(withdraw_id: int, tx_ref: str | None) -> dict:
    # fetch
    row = q("SELECT user_id, amount, status FROM withdrawals WHERE id=?", [withdraw_id])
    if not row:
        raise ValueError("Withdrawal not found")
    rec = row[0]
    if rec["status"] != "requested":
        raise ValueError("Only 'requested' can be approved")

    # move pending -> paid (reduce pending)
    exec1("UPDATE wallets SET pending_withdrawal = ROUND(pending_withdrawal - ?,2) WHERE user_id=?",
          [rec["amount"], rec["user_id"]])

    ts = datetime.utcnow().isoformat()
    exec1("UPDATE withdrawals SET status='paid', decided_at=?, tx_ref=? WHERE id=?",
          [ts, tx_ref, withdraw_id])
    return {"withdraw_id": withdraw_id, "status": "paid", "decided_at": ts, "tx_ref": tx_ref}

def reject_withdraw(withdraw_id: int, tx_ref: str | None = None) -> dict:
    row = q("SELECT user_id, amount, status FROM withdrawals WHERE id=?", [withdraw_id])
    if not row:
        raise ValueError("Withdrawal not found")
    rec = row[0]
    if rec["status"] != "requested":
        raise ValueError("Only 'requested' can be rejected")

    # refund: pending -> available
    exec1("UPDATE wallets SET pending_withdrawal = ROUND(pending_withdrawal - ?,2), "
          "available_balance = ROUND(available_balance + ?,2) WHERE user_id=?",
          [rec["amount"], rec["amount"], rec["user_id"]])

    ts = datetime.utcnow().isoformat()
    exec1("UPDATE withdrawals SET status='rejected', decided_at=?, tx_ref=? WHERE id=?",
          [ts, tx_ref, withdraw_id])
    return {"withdraw_id": withdraw_id, "status": "rejected", "decided_at": ts}

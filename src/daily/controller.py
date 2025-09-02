# src/daily/controller.py
from __future__ import annotations
from typing import Dict, Tuple
from uuid import uuid4
import math

# --- In-memory ledgers (dev only) ---
LEDGER_BALANCE: Dict[str, float] = {}            # user_id -> balance
LEDGER_BUNDLES: Dict[str, Dict] = {}             # bundle_id -> {user_id, plan, minutes}

# Simple rates (USD / minute) per task type
RATES_USD_PER_MIN: Dict[str, float] = {
    "micro_lesson": 0.02,
    "read_aloud":   0.01,
    "qr_proof":     0.015,
    "geo_ping":     0.01,
    "safety_tag":   0.015,
}

TASK_ORDER = ["safety_tag", "read_aloud", "qr_proof", "micro_lesson", "geo_ping"]

def allocate_plan(minutes: int) -> Dict[str, int]:
    """Very simple allocator: roughly even split across task types."""
    minutes = max(0, int(minutes))
    kinds = len(TASK_ORDER)
    base = minutes // kinds
    rem = minutes % kinds
    plan = {k: base for k in TASK_ORDER}
    for i in range(rem):
        plan[TASK_ORDER[i]] += 1
    # remove zero entries to keep payload small
    return {k: v for k, v in plan.items() if v > 0}

def estimate_usd(plan: Dict[str, int]) -> float:
    total = 0.0
    for k, m in plan.items():
        total += RATES_USD_PER_MIN.get(k, 0.0) * float(m)
    return round(total, 2)

def start_bundle(user_id: str, minutes: int) -> Tuple[str, Dict[str, int], float]:
    plan = allocate_plan(minutes)
    bundle_id = uuid4().hex[:8].upper()
    LEDGER_BUNDLES[bundle_id] = {
        "user_id": user_id,
        "plan": plan,
        "minutes": int(minutes),
    }
    paid_usd = estimate_usd(plan)
    return bundle_id, plan, paid_usd

def submit_bundle(user_id: str, bundle_id: str, results: Dict) -> Tuple[float, float]:
    meta = LEDGER_BUNDLES.get(bundle_id)
    if not meta or meta.get("user_id") != user_id:
        raise ValueError("Invalid bundle or owner mismatch")
    plan = meta["plan"]
    pay = estimate_usd(plan)

    # credit wallet (in-memory)
    prev = float(LEDGER_BALANCE.get(user_id, 0.0))
    new_bal = round(prev + pay, 2)
    LEDGER_BALANCE[user_id] = new_bal

    # one-time bundle — remove it
    LEDGER_BUNDLES.pop(bundle_id, None)

    return pay, new_bal

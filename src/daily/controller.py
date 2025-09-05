from __future__ import annotations
from typing import Dict, Tuple
from uuid import uuid4

from .rates import get_rates, get_targets

# In‑memory ledgers (dev only)
LEDGER_BALANCE: Dict[str, float] = {}                # user_id -> balance
LEDGER_BUNDLES: Dict[str, dict] = {}                 # bundle_id -> {user_id, plan, minutes}

# Preferred order (fast switching + verification friendly)
TASK_ORDER = ["safety_tag", "read_aloud", "qr_proof", "geo_ping", "micro_lesson"]

def _allocate_plan(minutes: int) -> Dict[str, int]:
    """
    Very simple greedy allocator that fills 'minutes' using task mix.
    Returns a dict of {task_type: total_seconds}.
    """
    rates = get_rates()
    secs_target = minutes * 60
    plan: Dict[str, int] = {k: 0 for k in TASK_ORDER}

    i = 0
    remaining = secs_target
    while remaining > 0 and i < len(TASK_ORDER):
        k = TASK_ORDER[i]
        sec = max(1, int(rates[k]["sec"]))
        # small batches to keep UI snappy
        batch = max(1, min(remaining // sec, 3 if k == "micro_lesson" else 8))
        taken = batch * sec
        plan[k] += taken
        remaining -= taken
        i = (i + 1) % len(TASK_ORDER)

        # stop when we are within 10s
        if remaining <= 10:
            break
    return {k: v for k, v in plan.items() if v > 0}

def start_bundle(user_id: str, minutes: int) -> Tuple[str, dict, Dict[str, int], int]:
    """
    Create a bundle, store in ledger, and return:
    (bundle_id, targets, plan, minutes)
    """
    targets = get_targets()
    minutes = max(targets["min_bundle_minutes"],
                  min(minutes or targets["default_bundle_minutes"],
                      targets["max_bundle_minutes"]))

    plan = _allocate_plan(minutes)
    bundle_id = f"BN_{uuid4().hex[:8].upper()}"
    LEDGER_BUNDLES[bundle_id] = {"user_id": user_id, "plan": plan, "minutes": minutes}
    return bundle_id, targets, plan, minutes

def _estimate_usd(plan: Dict[str, int]) -> float:
    rates = get_rates()
    total = 0.0
    for k, sec in plan.items():
        per = rates.get(k, {"usd": 0.0, "sec": 1})
        units = max(1, int(round(sec / max(1, int(per["sec"])))))
        total += units * float(per["usd"])
    return round(total, 2)

def submit_bundle(user_id: str, bundle_id: str, results: dict) -> Tuple[float, float]:
    """
    Validate owner, compute pay and credit wallet.
    results can be used later for QA; we ignore for now in dev mode.
    Returns (paid_usd, new_balance)
    """
    meta = LEDGER_BUNDLES.get(bundle_id)
    if not meta or meta["user_id"] != user_id:
        raise ValueError("Invalid bundle or owner mismatch")

    pay = _estimate_usd(meta["plan"])
    prev = float(LEDGER_BALANCE.get(user_id, 0.0))
    new_bal = round(prev + pay, 2)
    LEDGER_BALANCE[user_id] = new_bal

    # one‑time bundle
    LEDGER_BUNDLES.pop(bundle_id, None)
    return pay, new_bal

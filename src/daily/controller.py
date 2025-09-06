# src/daily/controller.py
from __future__ import annotations

import math
from typing import Dict, Tuple

from src.daily.rates import get_rates, get_targets
from src.wallet.models import UserCapabilities

# =========================
# In-memory ledgers (dev only)
# =========================
LEDGER_BALANCE: Dict[str, float] = {}  # user_id -> balance (USD)
LEDGER_BUNDLES: Dict[str, dict] = {}   # bundle_id -> {user_id, plan (secs), minutes}

# Base task order (fast switching + verification friendly)
TASK_ORDER_BASE: list[str] = [
    "safety_tag",
    "read_aloud",
    "qr_proof",
    "geo_ping",
    "micro_lesson",
    "prompt_rank",
]

def _choose_task_order(caps: UserCapabilities | None) -> list[str]:
    """
    Capability-aware task priority.
    Voice-first users → reading/voice tasks အရင်ပေးမယ်။
    """
    if caps and caps.prefers_voice:
        return ["read_aloud", "prompt_rank", "safety_tag", "qr_proof", "geo_ping", "micro_lesson"]
    return TASK_ORDER_BASE


def allocate_plan(minutes: int, caps: UserCapabilities | None = None) -> Dict[str, int]:
    """
    Very simple greedy allocator that fills `minutes` using typical task mix.
    Returns a dict of {task_type: total_seconds}.
    """
    rates = get_rates()                       # {"task": {"sec": int, "usd": float}, ...}
    order = _choose_task_order(caps)
    seconds = max(0, int(minutes) * 60)

    plan: Dict[str, int] = {k: 0 for k in order}
    i = 0
    remaining = seconds

    while remaining > 0 and i < len(order):
        k = order[i]
        task_sec = max(1, int(rates[k]["sec"]))      # minimal block per task
        # micro_lesson ကို batch အရွယ်အစား စုတိုးပေးပါ (ကျန်စsecs များအတွက် n*task_sec)
        batch = task_sec * (3 if k == "micro_lesson" else 1)

        if batch <= remaining:
            plan[k] += batch
            remaining -= batch
        else:
            # last chunk
            plan[k] += remaining
            remaining = 0

        # rotate
        i = (i + 1) % len(order)

        # escape — close enough
        if remaining <= min(10, task_sec // 2):
            break

    return plan


def _estimate_usd(plan: Dict[str, int]) -> float:
    """
    Plan (seconds) ကို USD ထဲပြောင်းတွက်မယ်။
    """
    rates = get_rates()
    total = 0.0
    for k, sec in plan.items():
        unit_sec = max(1, int(rates[k]["sec"]))
        unit_usd = float(rates[k]["usd"])
        # sec တစ်ခုချင်းကို unit တိုင်းပေါင်း (rounded)
        units = sec / unit_sec
        total += units * unit_usd
    return round(total, 2)


def start_bundle(user_id: str, minutes: int, caps: UserCapabilities | None = None) -> Tuple[str, dict, int]:
    """
    Create a earning bundle for a user.
    Returns: (bundle_id, targets_dict, bundle_minutes)
    """
    targets = get_targets()
    # minutes guard (min/max)
    min_m = int(targets.get("min_bundle_minutes", 10))
    max_m = int(targets.get("max_bundle_minutes", 120))
    bundle_minutes = max(min_m, min(int(minutes), max_m))

    plan = allocate_plan(bundle_minutes, caps)

    # simple bundle id (dev only)
    import uuid
    bundle_id = uuid.uuid4().hex[:18].upper()

    LEDGER_BUNDLES[bundle_id] = {
        "user_id": user_id,
        "plan": plan,                 # seconds per task
        "minutes": bundle_minutes,
        "est_usd": _estimate_usd(plan),
    }

    return bundle_id, targets, bundle_minutes


def submit_bundle(user_id: str, bundle_id: str, results: dict) -> Tuple[float, float]:
    """
    Finalize bundle → credit wallet (in-memory).
    Returns: (paid_usd, new_balance)
    """
    meta = LEDGER_BUNDLES.get(bundle_id)
    if not meta or meta["user_id"] != user_id:
        raise ValueError("Invalid bundle or owner mismatch")

    pay = _estimate_usd(meta["plan"])
    prev = float(LEDGER_BALANCE.get(user_id, 0.0))
    new_bal = round(prev + pay, 2)
    LEDGER_BALANCE[user_id] = new_bal

    # one-time bundle
    LEDGER_BUNDLES.pop(bundle_id, None)
    return pay, new_bal

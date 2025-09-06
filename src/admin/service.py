# src/admin/service.py
from typing import Dict, Tuple

# in‑memory data from daily flow
from src.daily.controller import LEDGER_BUNDLES  # {bundle_id: {"user_id", "plan", "minutes"}}
from src.daily.rates import get_rates            # {"task": {"sec": int, "usd": float}}

# ---- helpers ---------------------------------------------------------------

def _expand_plan_to_stats(plan: Dict[str, int], rates: Dict[str, Dict[str, float]]
                          ) -> Tuple[Dict[str, int], int, float]:
    """
    plan: {"read_aloud": minutes, ...}
    rates: {"read_aloud": {"sec": 20, "usd": 0.75}, ...}
    return: (task_counts, total_minutes, total_usd)
    """
    task_counts: Dict[str, int] = {}
    total_minutes = 0
    total_usd = 0.0

    for task, mins in plan.items():
        if mins <= 0 or task not in rates:
            continue
        sec_per_task = int(rates[task]["sec"])
        usd_per_task = float(rates[task]["usd"])

        # how many tasks can be performed within allocated minutes
        total_seconds = int(mins) * 60
        count = total_seconds // max(1, sec_per_task)

        task_counts[task] = task_counts.get(task, 0) + int(count)
        total_minutes += int(mins)
        total_usd += count * usd_per_task

    return task_counts, total_minutes, round(total_usd, 2)

# ---- public API for admin --------------------------------------------------

def summarize_earnings(user_id: str) -> Dict[str, object]:
    """
    Aggregate across all bundles owned by user_id.
    """
    rates = get_rates()
    all_counts: Dict[str, int] = {}
    minutes_sum = 0
    usd_sum = 0.0

    for b in LEDGER_BUNDLES.values():
        if b.get("user_id") != user_id:
            continue
        plan = b.get("plan", {})
        counts, m, u = _expand_plan_to_stats(plan, rates)
        minutes_sum += m
        usd_sum += u
        for k, v in counts.items():
            all_counts[k] = all_counts.get(k, 0) + v

    return {
        "usd": round(usd_sum, 2),
        "minutes": minutes_sum,
        "task_count": sum(all_counts.values()),
        "by_task": all_counts,
        # placeholder (wallet integration can flip this later)
        "voice_mode": False,
    }


def summarize_tasks(user_id: str) -> Dict[str, int]:
    """
    Return only {task_type: count} across user bundles.
    """
    rates = get_rates()
    totals: Dict[str, int] = {}

    for b in LEDGER_BUNDLES.values():
        if b.get("user_id") != user_id:
            continue
        plan = b.get("plan", {})
        counts, _, _ = _expand_plan_to_stats(plan, rates)
        for k, v in counts.items():
            totals[k] = totals.get(k, 0) + v

    return totals

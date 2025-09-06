from __future__ import annotations
from datetime import datetime
from typing import Dict, Any

# In‑memory monthly contribution holds: {(user_id, "YYYY-MM"): amount}
_CONTRI_HOLDS: Dict[tuple, float] = {}

def _safe_call(fn_name: str, *args, **kwargs):
    """
    Try calling provider from existing daily/classic modules if available.
    If not present, return 0. This keeps aggregator robust while modules evolve.
    Expected provider signatures (optional in your codebase):
      - daily.controller.get_totals(user_id) -> {"today":x,"week":y,"month":z}
      - classic.controller.get_totals(user_id) -> {"today":x,"week":y,"month":z}
    """
    try:
        # daily
        if fn_name == "daily_totals":
            from daily import controller as dctl  # type: ignore
            if hasattr(dctl, "get_totals"):
                return dctl.get_totals(*args, **kwargs)
        # classic
        if fn_name == "classic_totals":
            from classic import controller as cctl  # type: ignore
            if hasattr(cctl, "get_totals"):
                return cctl.get_totals(*args, **kwargs)
    except Exception:
        pass
    # Fallback zeros
    return {"today": 0.0, "week": 0.0, "month": 0.0}

def get_earnings_breakdown(user_id: str) -> Dict[str, Any]:
    """Merge classic + daily into a single breakdown dict."""
    daily = _safe_call("daily_totals", user_id=user_id)
    classic = _safe_call("classic_totals", user_id=user_id)

    today = float(daily.get("today", 0)) + float(classic.get("today", 0))
    week  = float(daily.get("week", 0))  + float(classic.get("week", 0))
    month = float(daily.get("month", 0)) + float(classic.get("month", 0))

    return {
        "classic": {"today": float(classic.get("today", 0)), "week": float(classic.get("week", 0)), "month": float(classic.get("month", 0))},
        "daily":   {"today": float(daily.get("today", 0)),   "week": float(daily.get("week", 0)),   "month": float(daily.get("month", 0))},
        "today": today, "week": week, "month": month,
    }

def apply_monthly_contribution(user_id: str, month: str, amount: float = 100.0) -> Dict[str, Any]:
    """
    Hold monthly contribution (default $100). Idempotent per (user, month).
    """
    key = (user_id, month)
    if key not in _CONTRI_HOLDS:
        _CONTRI_HOLDS[key] = float(amount)
    held = _CONTRI_HOLDS[key]
    # Withdrawable is month_earn - held (never below zero)
    brk = get_earnings_breakdown(user_id)
    month_earn = float(brk.get("month", 0.0))
    withdrawable = max(0.0, month_earn - held)
    return {"user_id": user_id, "month": month, "held": held, "month_earn": month_earn, "withdrawable": withdrawable}

def get_wallet_summary(user_id: str) -> Dict[str, Any]:
    """
    Summarize wallet for dashboard. With no DB yet, total_earn ~= month_earn (MVP).
    Later, replace with DB lifetime sum.
    """
    brk = get_earnings_breakdown(user_id)
    month_earn = float(brk.get("month", 0.0))
    month_key = datetime.utcnow().strftime("%Y-%m")
    held = _CONTRI_HOLDS.get((user_id, month_key), 0.0)
    withdrawable = max(0.0, month_earn - held)
    return {
        "user_id": user_id,
        "total_earn": month_earn,     # TODO: swap to lifetime when DB wired
        "month_earn": month_earn,
        "contribution_held": held,
        "withdrawable": withdrawable,
        "breakdown": brk,
    }

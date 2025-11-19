# src/safety/risk.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import os, time

# ---- Tunables (ENV) ----
RISK_FACE_TH_USD = float(os.getenv("RISK_FACE_TH_USD", "5.0"))        # >= ဒီပမာဏ face required
RISK_DAY_CAP_USD = float(os.getenv("RISK_DAY_CAP_USD", "100.0"))      # တနေ့လျှင် အများဆုံး USD
RISK_TX_PER_HOUR = int(os.getenv("RISK_TX_PER_HOUR", "6"))            # တနာရီလျှင် အများဆုံး တင် /ဖြုတ်
RISK_NEWUSER_AGE_H = int(os.getenv("RISK_NEWUSER_AGE_H", "24"))       # အသစ်သုံးသူအား အထူးကာကွယ်

@dataclass
class RiskResult:
    action: str        # "allow" | "challenge_face" | "block"
    score: float       # 0..1 (မြင့်程危险)
    reasons: list[str]
    require_face: bool

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

# ---- Hooks to your DB/metrics (safe defaults) ----
def _get_user_stats(user_id: str) -> Dict[str, Any]:
    """
    TODO: wire to DB. Safe defaults now.
    return dict(age_hours=..., tx_count_last_hour=..., sum_withdraw_day=...)
    """
    return {"age_hours": 48, "tx_count_last_hour": 0, "sum_withdraw_day": 0.0}

def assess_withdraw_risk(*, user_id: str, device_id: str, amount: float, ip_hash: Optional[str]=None) -> RiskResult:
    s = _get_user_stats(user_id)
    score = 0.0
    reasons: list[str] = []

    if amount >= RISK_FACE_TH_USD:
        score += 0.35; reasons.append(f"amount>={RISK_FACE_TH_USD}")
    if s["sum_withdraw_day"] + amount > RISK_DAY_CAP_USD:
        score += 0.5; reasons.append("day_cap_exceeded")
    if s["tx_count_last_hour"] >= RISK_TX_PER_HOUR:
        score += 0.3; reasons.append("rate_high")
    if s["age_hours"] < RISK_NEWUSER_AGE_H:
        score += 0.25; reasons.append("new_user")

    # normalize & decide
    score = max(0.0, min(1.0, score))
    if score >= 0.50:
        return RiskResult(action="challenge_face", score=score, reasons=reasons, require_face=True)
    if score >= 0.85:
        return RiskResult(action="block", score=score, reasons=reasons, require_face=True)
    return RiskResult(action="allow", score=score, reasons=reasons, require_face=(amount >= RISK_FACE_TH_USD))

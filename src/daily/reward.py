# src/daily/reward.py
from datetime import datetime
from decimal import Decimal

def compute_reward(base_usd: float, streak_days: int = 0, ai_assist: bool = False, sponsor: bool = False):
    """Compute final reward with streak, AI assist, and sponsor multipliers."""
    reward = Decimal(str(base_usd))

    # 🔥 Streak bonus
    if streak_days >= 5:
        reward *= Decimal("1.10")
    elif streak_days >= 10:
        reward *= Decimal("1.20")

    # 🤖 AI assist bonus
    if ai_assist:
        reward *= Decimal("1.15")

    # 💰 Sponsor bonus
    if sponsor:
        reward *= Decimal("1.30")

    # 🏦 Platform fee (10%)
    fee_cut = reward * Decimal("0.10")
    net = reward - fee_cut

    return {
        "gross_usd": float(round(reward, 2)),
        "platform_fee": float(round(fee_cut, 2)),
        "net_usd": float(round(net, 2)),
        "timestamp": datetime.utcnow().isoformat()
    }

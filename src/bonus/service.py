# src/bonus/service.py
from __future__ import annotations
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.bonus.logic import BonusEngine, default_rules, BonusTrigger, UserContext
from src.utils.money import as_money
from src.db.models import WalletLedger, LedgerType
from src.config.settings import BONUS_DAILY_CAP_USD  # Decimal-compatible

# wallet/bonus adapter (ledger writer with idempotency)
from src.wallet.bonus import apply_bonus  # async def apply_bonus(session, user_id, base_amount_usd, ref=None, meta=None) -> tuple[Decimal, Optional[str]]

engine = BonusEngine(default_rules())

# -------- helpers pulling today's state --------

async def _today_bonus_total(session: AsyncSession, user_id: str) -> Decimal:
    q = (
        select(func.coalesce(func.sum(WalletLedger.amount_usd), 0))
        .where(WalletLedger.user_id == user_id)
        .where(WalletLedger.type == LedgerType.BONUS)
        .where(func.date(WalletLedger.created_at) == datetime.now(timezone.utc).date())
    )
    value = (await session.execute(q)).scalar_one()
    return as_money(value or 0)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# -------- public orchestration APIs --------

async def grant_daily_submit_bonus(
    session: AsyncSession,
    *,
    user_id: str,
    base_usd: Decimal,
    user_flags: Dict[str, Any],
    source_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a plan for DAILY_SUBMIT_OK and persist each line into wallet ledger (BONUS type).
    Idempotent per (user_id, rule, day, source_id).
    """
    # 1) gather user context
    today_total = await _today_bonus_total(session, user_id)
    user = UserContext(
        user_id=user_id,
        is_trust_ok=bool(user_flags.get("is_trust_ok", True)),
        is_kyc_ok=bool(user_flags.get("is_kyc_ok", True)),
        today_bonus_granted_usd=today_total,
    )

    # 2) plan
    plan = engine.plan(
        event=BonusTrigger.DAILY_SUBMIT_OK,
        user=user,
        base_value_usd=as_money(base_usd),
        day_cap_usd=as_money(Decimal(str(BONUS_DAILY_CAP_USD))) if BONUS_DAILY_CAP_USD is not None else None,
        source_id=source_id,
        tags=["assist"],
    )
    if plan.is_zero:
        return {"ok": True, "granted": "0.00", "lines": [], "capped": plan.capped_by_daily, "ts": _now_iso()}

    # 3) persist each line (AUDIT-READY). We reuse wallet.bonus.apply_bonus to enforce idempotency.
    applied = []
    for ln in plan.lines:
        # we pass the computed line amount directly as base for the adapter (it may simply write it)
        amt, ledger_id = await apply_bonus(
            session,
            user_id=user_id,
            base_amount_usd=ln.amount_usd,
            ref=ln.meta.get("idem_key"),  # unique key per line
            meta={**ln.meta, "rule": ln.rule.name, "generated_at": plan.generated_at.isoformat()},
        )
        if amt and amt > 0:
            applied.append({
                "rule": ln.rule.name,
                "amount_usd": str(amt),
                "idem_key": ln.meta.get("idem_key"),
                "ledger_id": ledger_id,
            })

    total = as_money(sum(Decimal(x["amount_usd"]) for x in applied) if applied else Decimal("0"))
    return {
        "ok": True,
        "granted": str(total),
        "lines": applied,
        "capped": plan.capped_by_daily,
        "ts": _now_iso(),
    }

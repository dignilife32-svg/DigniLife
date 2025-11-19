# src/bonus/logic.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, date
import hashlib
from decimal import Decimal

# use your central money helpers (2 d.p, HALF_UP)
from src.utils.money import as_money  # -> Decimal(2dp)
# if you also export Q2 in utils, keep it; we don't need it directly here.

# ---------------- Enums ----------------

class BonusTrigger(str, Enum):
    DAILY_SUBMIT_OK = "DAILY_SUBMIT_OK"
    EARN_COMMIT    = "EARN_COMMIT"
    SYSTEM_PROMO   = "SYSTEM_PROMO"

class BonusCalcKind(str, Enum):
    FIXED    = "FIXED"
    PCT      = "PCT"
    TIERLESS = "TIERLESS"  # global single flat rate (fallback)

# ---------------- Rule Model ----------------

@dataclass(frozen=True)
class BonusRule:
    name: str
    trigger: BonusTrigger
    kind: BonusCalcKind

    fixed_usd: Optional[Decimal] = None         # for FIXED
    pct: Optional[Decimal] = None               # e.g. Decimal("0.03") == 3%
    min_per_event: Optional[Decimal] = None
    max_per_event: Optional[Decimal] = None

    require_trust: bool = False
    require_kyc_ok: bool = False
    tags: tuple[str, ...] = ()

    def compute(self, *, base_value: Decimal) -> Decimal:
        """Return money(amt) based on rule kind + clamp by min/max."""
        if self.kind == BonusCalcKind.FIXED:
            amt = self.fixed_usd or Decimal("0.00")
        elif self.kind == BonusCalcKind.PCT:
            pct = self.pct or Decimal("0.00")
            amt = base_value * pct
        else:  # TIERLESS – default $0.05 unless overridden by settings layer
            # keep small non-zero default so engine always yields a line
            amt = Decimal("0.05")

        # clamp
        if self.min_per_event is not None:
            amt = max(amt, self.min_per_event)
        if self.max_per_event is not None:
            amt = min(amt, self.max_per_event)
        return as_money(amt)

# ---------------- Inputs / Outputs ----------------

@dataclass(frozen=True)
class UserContext:
    user_id: str
    is_trust_ok: bool = True
    is_kyc_ok: bool = True
    today_bonus_granted_usd: Decimal = Decimal("0.00")  # already granted today

@dataclass(frozen=True)
class BonusplanLine:
    rule: BonusRule
    amount_usd: Decimal
    reason: str
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Bonusplan:
    event: BonusTrigger
    base_value_usd: Decimal
    lines: List[BonusplanLine]
    total_usd: Decimal
    capped_by_daily: bool
    generated_at: datetime

    @property
    def is_zero(self) -> bool:
        return self.total_usd <= Decimal("0.00")

# ---------------- Engine ----------------

class BonusEngine:
    def __init__(self, rules: List[BonusRule]):
        self._rules = tuple(rules)

    @staticmethod
    def _today_iso() -> str:
        return date.today().isoformat()

    @staticmethod
    def _idem(user_id: str, source_id: str, rule_name: str, day_iso: str) -> str:
        raw = f"{user_id}|{source_id}|{rule_name}|{day_iso}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def plan(
        self,
        *,
        event: BonusTrigger,
        user: UserContext,
        base_value_usd: Decimal,
        day_cap_usd: Optional[Decimal] = None,
        source_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Bonusplan:
        """Build a plan (pure, no I/O). Scales proportionally if daily cap reached."""
        today = self._today_iso()
        base_value_usd = as_money(base_value_usd)
        tags = tags or []

        # 1) filter eligible rules
        eligible: List[BonusplanLine] = []
        for r in self._rules:
            if r.trigger != event:
                continue
            if r.require_trust and not user.is_trust_ok:
                continue
            if r.require_kyc_ok and not user.is_kyc_ok:
                continue
            amt = r.compute(base_value=base_value_usd)
            if amt <= Decimal("0.00"):
                continue
            line = BonusplanLine(
                rule=r,
                amount_usd=amt,
                reason=f"bonus:{event.value}",
                meta={
                    "tags": list(set(tags + list(r.tags))),
                },
            )
            eligible.append(line)

        subtotal = as_money(sum((ln.amount_usd for ln in eligible), Decimal("0.00")))
        if not eligible:
            return Bonusplan(event, base_value_usd, [], Decimal("0.00"), False, datetime.now(timezone.utc))

        # 2) enforce user daily cap (across all rules)
        already = as_money(user.today_bonus_granted_usd)
        cap = day_cap_usd
        capped = False
        total = subtotal
        lines = eligible

        if cap is not None:
            remaining = as_money(max(Decimal("0.00"), cap - already))
            if remaining <= Decimal("0.00"):
                # nothing left today
                return Bonusplan(event, base_value_usd, [], Decimal("0.00"), True, datetime.now(timezone.utc))
            if subtotal > remaining:
                # proportional scale-down
                factor = (remaining / subtotal) if subtotal > 0 else Decimal("0.00")
                new_lines: List[BonusplanLine] = []
                for ln in eligible:
                    new_amt = as_money(ln.amount_usd * factor)
                    if new_amt <= Decimal("0.00"):
                        continue
                    meta = dict(ln.meta)
                    meta["scaled_factor"] = str(factor)
                    new_lines.append(BonusplanLine(rule=ln.rule, amount_usd=new_amt, reason=ln.reason, meta=meta))
                lines = new_lines
                total = as_money(sum((ln.amount_usd for ln in lines), Decimal("0.00")))
                capped = True

        # 3) attach idem_key per line
        src = source_id or f"{event.value}:{today}"
        with_idem: List[BonusplanLine] = []
        for ln in lines:
            meta = dict(ln.meta)
            meta["idem_key"] = self._idem(user.user_id, src, ln.rule.name, today)
            meta["source_id"] = src
            meta["day"] = today
            with_idem.append(BonusplanLine(rule=ln.rule, amount_usd=ln.amount_usd, reason=ln.reason, meta=meta))

        return Bonusplan(
            event=event,
            base_value_usd=base_value_usd,
            lines=with_idem,
            total_usd=as_money(total),
            capped_by_daily=capped,
            generated_at=datetime.now(timezone.utc),
        )

# ---------------- Default Rules (editable) ----------------

def default_rules() -> List[BonusRule]:
    return [
        # Flat (tierless) $0.05 on successful daily submit (trust+kyc gated)
        BonusRule(
            name="daily_flat",
            trigger=BonusTrigger.DAILY_SUBMIT_OK,
            kind=BonusCalcKind.TIERLESS,
            min_per_event=as_money(Decimal("0.05")),
            max_per_event=as_money(Decimal("0.50")),
            require_trust=True,
            require_kyc_ok=True,
            tags=("daily", "flat", "tierless"),
        ),
        # 3% of earn commit, capped $0.25 per event
        BonusRule(
            name="earn_commit_pct",
            trigger=BonusTrigger.EARN_COMMIT,
            kind=BonusCalcKind.PCT,
            pct=Decimal("0.03"),
            max_per_event=as_money(Decimal("0.25")),
            require_trust=True,
            require_kyc_ok=True,
            tags=("earn", "pct"),
        ),
        # System promo fixed $0.20 (no gate)
        BonusRule(
            name="promo_fixed",
            trigger=BonusTrigger.SYSTEM_PROMO,
            kind=BonusCalcKind.FIXED,
            fixed_usd=as_money(Decimal("0.20")),
            max_per_event=as_money(Decimal("0.20")),
            tags=("promo",),
        ),
    ]

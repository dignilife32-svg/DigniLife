# src/wallet/service.py
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from hashlib import blake2b
from typing import Optional, Tuple
from src.wallet.bonus import apply_bonus

from sqlalchemy import select, func, literal, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as pg_insert  # for upserts

from src.wallet.models import WalletLedger, LedgerType  # keep your existing models

from src.utils.money import as_money, q2, q4
from src.config import settings  # where DAILY_OUT etc. lives

# ---- Config ---------------------------------------------------------------

DAILY_OUT: Decimal = as_money(getattr(settings, "DAILY_OUT", "3.333333"))  # fallback

# ---- Helpers --------------------------------------------------------------

def make_idem(user_id: str, kind: str, payload: str = "") -> str:
    """
    Stable idempotency key: same (user, kind, payload) -> same key.
    """
    h = blake2b(digest_size=16)
    h.update(f"{user_id}|{kind}|{payload}".encode("utf-8"))
    return h.hexdigest()

def utc_today() -> datetime.date:
    return datetime.now(timezone.utc).date()

# ---- Queries --------------------------------------------------------------

async def _sums(session: AsyncSession, user_id: str) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Return (earn_commits, withdraw_commits, active_reserves) in USD.
    """
    # Compute three sums in a single round‑trip using filtered aggregates
    stmt = (
        select(
            func.coalesce(
                func.sum(
                    func.case(
                        (WalletLedger.ltype == LedgerType.EARN_COMMIT, WalletLedger.amount_usd),
                        else_=literal(0),
                    )
                ), 0
            ).label("earn"),
            func.coalesce(
                func.sum(
                    func.case(
                        (WalletLedger.ltype == LedgerType.WITHDRAW_COMMIT, WalletLedger.amount_usd),
                        else_=literal(0),
                    )
                ), 0
            ).label("withdraw"),
            func.coalesce(
                func.sum(
                    func.case(
                        (WalletLedger.ltype == LedgerType.EARN_RESERVE, WalletLedger.amount_usd),
                        (WalletLedger.ltype == LedgerType.WITHDRAW_RESERVE, WalletLedger.amount_usd),
                        # reversed/committed rows should be separate types, so reserves remaining only
                        else_=literal(0),
                    )
                ), 0
            ).label("reserves"),
        )
        .where(WalletLedger.user_id == user_id)
    )
    row = (await session.execute(stmt)).one()
    earn = as_money(row.earn)
    wd   = as_money(row.withdraw)
    res  = as_money(row.reserves)
    return q4(earn), q4(wd), q4(res)

async def get_balance(session: AsyncSession, user_id: str) -> Decimal:
    """
    Available USD balance: earn_commits - withdraw_commits - active_reserves
    """
    earn, wd, res = await _sums(session, user_id)
    return q2(earn - wd - res)

# ---- Writes (all transactional & idempotent) ------------------------------

async def _post_ledger(
    session: AsyncSession,
    *,
    user_id: str,
    amount_usd: Decimal,
    ltype: LedgerType,
    idem_key: str,
    ref_task_code: Optional[str] = None,
    payload_hash: Optional[str] = None,
) -> WalletLedger:
    """
    Insert a ledger row (idempotent). Requires UNIQUE (user_id, idem_key, ltype).
    """
    amount_usd = q4(as_money(amount_usd))

    # Try insert; if conflict on idem_key -> return existing row
    stmt = pg_insert(WalletLedger).values(
        user_id=user_id,
        amount_usd=amount_usd,
        ltype=ltype,
        idem_key=idem_key,
        ref_task_code=ref_task_code,
        payload_hash=payload_hash,
        event_date=utc_today(),
    ).on_conflict_do_nothing(index_elements=["user_id", "idem_key", "ltype"]).returning(WalletLedger)
    res = await session.execute(stmt)
    row = res.scalar_one_or_none()
    if row:
        return row

    # If not returned, there is already a row; fetch it
    get_stmt = select(WalletLedger).where(
        and_(
            WalletLedger.user_id == user_id,
            WalletLedger.idem_key == idem_key,
            WalletLedger.ltype == ltype,
        )
    )
    row = (await session.execute(get_stmt)).scalar_one()
    return row

# Earn flow ---------------------------------------------------------------

async def reserve_earn(
    session: AsyncSession, *, user_id: str, amount: Decimal, task_code: str, payload_hash: str = ""
) -> WalletLedger:
    idem = make_idem(user_id, "EARN_RESERVE", payload_hash or task_code)
    async with session.begin():
        return await _post_ledger(
            session,
            user_id=user_id,
            amount_usd=q4(amount),  # reserves are positive
            ltype=LedgerType.EARN_RESERVE,
            idem_key=idem,
            ref_task_code=task_code,
            payload_hash=payload_hash,
        )

async def commit_earn(
    session: AsyncSession, *, user_id: str, amount: Decimal, task_code: str, payload_hash: str = ""
) -> WalletLedger:
    idem = make_idem(user_id, "EARN_COMMIT", payload_hash or task_code)
    async with session.begin():
        # Optionally clear paired reserve here if your design requires it
        return await _post_ledger(
            session,
            user_id=user_id,
            amount_usd=q4(amount),
            ltype=LedgerType.EARN_COMMIT,
            idem_key=idem,
            ref_task_code=task_code,
            payload_hash=payload_hash,
        )
    # === NEW: auto bonus ===
    try:
        bonus_amt, bonus_id = await apply_bonus(
            session, user_id, as_money(base_value),
            ref=task_code, meta={"source": "auto", "earn_ledger": ledger_id}
        )
        if bonus_amt > 0:
            # (optional) log or append to response
            pass
    except Exception:
        # never fail the main earn; bonus is best-effort
        pass

    return ledger_id

async def reverse_earn(
    session: AsyncSession, *, user_id: str, amount: Decimal, task_code: str, payload_hash: str = ""
) -> WalletLedger:
    idem = make_idem(user_id, "EARN_REVERSE", payload_hash or task_code)
    async with session.begin():
        # reverse is negative of commit
        return await _post_ledger(
            session,
            user_id=user_id,
            amount_usd=q4(amount) * Decimal("-1"),
            ltype=LedgerType.EARN_REVERSE,
            idem_key=idem,
            ref_task_code=task_code,
            payload_hash=payload_hash,
        )

# Withdraw flow -----------------------------------------------------------

async def reserve_withdraw(
    session: AsyncSession, *, user_id: str, amount: Decimal, request_id: str
) -> WalletLedger:
    amount = q4(amount)
    idem = make_idem(user_id, "WITHDRAW_RESERVE", request_id)
    async with session.begin():
        # Balance check with lock (best effort; SQLAlchemy 2.0 async + PG)
        available = await get_balance(session, user_id)
        if available < amount:
            raise ValueError("Insufficient available balance")
        return await _post_ledger(
            session,
            user_id=user_id,
            amount_usd=amount,  # reserve recorded as positive hold
            ltype=LedgerType.WITHDRAW_RESERVE,
            idem_key=idem,
            payload_hash=request_id,
        )

async def commit_withdraw(
    session: AsyncSession, *, user_id: str, amount: Decimal, request_id: str
) -> WalletLedger:
    idem = make_idem(user_id, "WITHDRAW_COMMIT", request_id)
    async with session.begin():
        # commit as negative
        return await _post_ledger(
            session,
            user_id=user_id,
            amount_usd=q4(amount) * Decimal("-1"),
            ltype=LedgerType.WITHDRAW_COMMIT,
            idem_key=idem,
            payload_hash=request_id,
        )

async def reverse_withdraw(
    session: AsyncSession, *, user_id: str, amount: Decimal, request_id: str
) -> WalletLedger:
    idem = make_idem(user_id, "WITHDRAW_REVERSE", request_id)
    async with session.begin():
        # give money back (positive)
        return await _post_ledger(
            session,
            user_id=user_id,
            amount_usd=q4(amount),
            ltype=LedgerType.WITHDRAW_REVERSE,
            idem_key=idem,
            payload_hash=request_id,
        )

# Public API --------------------------------------------------------------

async def get_user_usd_balance(user_id: str, session: AsyncSession) -> Decimal:
    """
    External callers use this for wallet/summary etc.
    """
    return await get_balance(session, user_id)

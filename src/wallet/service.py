#src/wallet/service.py
from __future__ import annotations
import uuid
from decimal import Decimal
from typing import Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# ---- Helpers ----
def _n(v: Decimal | float | int) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"))


async def _select_one(session: AsyncSession, sql: str, **params):
    res = await session.execute(text(sql), params)
    return res.fetchone()


async def _exec(session: AsyncSession, sql: str, **params):
    await session.execute(text(sql), params)


async def _insert(session: AsyncSession, *, user_id: str, amount_usd: Decimal, note: str, ref: str) -> str:
    if ref:
        row = await _select_one(session, "SELECT id FROM wallet_ledger WHERE user_id=:u AND ref=:r LIMIT 1", u=user_id, r=ref)
        if row:
            return row[0]
    lid = uuid.uuid4().hex
    await _exec(
        session,
        """INSERT INTO wallet_ledger (id,user_id,amount_usd,note,ref,created_at)
           VALUES (:id,:u,:a,:n,:r,datetime('now'))""",
        id=lid,
        u=user_id,
        a=float(amount_usd),
        n=note,
        r=ref,
    )
    return lid


# ---- Queries ----
async def _sums(session: AsyncSession, user_id: str) -> Tuple[Decimal, Decimal, Decimal]:
    earn = _n((await _select_one(session, "SELECT COALESCE(SUM(CASE WHEN note LIKE 'EARN%' THEN amount_usd WHEN note='ADJUST' AND amount_usd>0 THEN amount_usd ELSE 0 END),0) FROM wallet_ledger WHERE user_id=:u", u=user_id))[0])
    wd = _n((await _select_one(session, "SELECT COALESCE(SUM(CASE WHEN note LIKE 'WITHDRAW_COMMIT%' THEN -amount_usd ELSE 0 END),0) FROM wallet_ledger WHERE user_id=:u", u=user_id))[0])
    resv = _n((await _select_one(session, "SELECT COALESCE(SUM(CASE WHEN note='WITHDRAW_RESERVE' THEN amount_usd WHEN note='RESERVE_RELEASE' THEN -amount_usd ELSE 0 END),0) FROM wallet_ledger WHERE user_id=:u", u=user_id))[0])
    return earn, wd, resv


async def get_user_usd_balance(*, user_id: str, session: AsyncSession) -> Decimal:
    e, w, r = await _sums(session, user_id)
    return _n(e - w - r)


# ---- Writes ----
async def add_earning(*, session: AsyncSession, user_id: str, amount_usd: float | Decimal, note: str = "EARN", request_id: str = "") -> str:
    async with session.begin():
        return await _insert(session, user_id=user_id, amount_usd=_n(amount_usd), note=note, ref=request_id)


async def add_adjustment(*, session: AsyncSession, user_id: str, amount_usd: float | Decimal, note: str = "ADJUST", request_id: str = "") -> str:
    async with session.begin():
        return await _insert(session, user_id=user_id, amount_usd=_n(amount_usd), note=note, ref=request_id)


async def create_withdraw_reserve(*, session: AsyncSession, user_id: str, amount_usd: float | Decimal, note: str = "WITHDRAW_RESERVE", request_id: str = "") -> str:
    amt = _n(amount_usd)
    async with session.begin():
        if (await get_user_usd_balance(user_id=user_id, session=session)) < amt:
            raise ValueError("insufficient available balance")
        return await _insert(session, user_id=user_id, amount_usd=amt, note=note, ref=request_id)


async def release_funds(*, session: AsyncSession, user_id: str, amount_usd: float | Decimal, note: str = "RESERVE_RELEASE", request_id: str = "") -> str:
    async with session.begin():
        return await _insert(session, user_id=user_id, amount_usd=_n(-abs(amount_usd)), note=note, ref=request_id)


async def commit_withdraw(*, session: AsyncSession, user_id: str, amount_usd: float | Decimal, note: str = "WITHDRAW_COMMIT", request_id: str = "") -> str:
    amt = _n(amount_usd)
    async with session.begin():
        if (await get_user_usd_balance(user_id=user_id, session=session)) < amt:
            raise ValueError("insufficient available balance")
        return await _insert(session, user_id=user_id, amount_usd=_n(-amt), note=note, ref=request_id)


async def reverse_withdraw(*, session: AsyncSession, user_id: str, amount_usd: float | Decimal, request_id: str = "") -> str:
    async with session.begin():
        return await _insert(session, user_id=user_id, amount_usd=_n(abs(amount_usd)), note="WITHDRAW_REVERSE", ref=request_id)


# ---- AI-Driven Global Payout Layer ----
async def payout_dispatch(user_id: str, amount: float, method: str, target: str) -> dict:
    method = method.lower()
    if method == "bank":
        return {"status": "PENDING", "message": f"Bank transfer queued for review: {target}"}
    if method == "ewallet":
        return {"status": "APPROVED", "message": f"E-wallet transfer sent to {target}"}
    if method == "prepaid_card":
        return {"status": "APPROVED", "message": f"Prepaid card {target} credited"}
    if method == "store_cash":
        code = f"STORE-{uuid.uuid4().hex[:6].upper()}"
        return {"status": "READY_FOR_PICKUP", "store": target, "pickup_code": code}
    if method == "unbanked_ai_cash":
        token = f"DIGNICASH-{uuid.uuid4().hex[:8].upper()}"
        return {"status": "AI_CASH", "token": token, "message": "Collect via local DigniLife partner"}
    return {"status": "UNKNOWN_METHOD", "message": "Unsupported payout method"}

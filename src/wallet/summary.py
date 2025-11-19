# src/wallet/summary.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from src.utils.currency import get_currency_display, convert_usd_to
from src.wallet.service import get_user_usd_balance  # <-- your existing service

router = APIRouter(prefix="/wallet", tags=["wallet"])


def require_user(x_user_id: str | None = Header(default=None, alias="x-user-id")) -> str:
    """
    Require x-user-id header. Raise 400 if missing.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="x-user-id header is required",
        )
    return x_user_id


@router.get("/summary")
async def wallet_summary(request: Request, user_id: str = Depends(require_user)):
    """
    Return balances in USD + Local (auto-detected via IP).
    """
    # 1) core balance (in USD)
    usd_balance: float = await get_user_usd_balance(user_id)

    # 2) detect currency from client IP and compute local balance
    client_ip = request.client.host if request.client else "127.0.0.1"
    currency_info = get_currency_display(client_ip)
    local_balance = convert_usd_to(currency_info["currency"], usd_balance)

    return {
        "usd_balance": usd_balance,
        "local_balance": local_balance,
        "currency": currency_info["currency"],
        "symbol": currency_info["symbol"],
        "fx_rate": currency_info["fx_rate"],
    }


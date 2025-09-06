from fastapi import APIRouter, Header, HTTPException, Query
from .service import get_wallet_summary, apply_monthly_contribution

router = APIRouter()

def _uid(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    return x_user_id

@router.get("/summary")
def wallet_summary(x_user_id: str | None = Header(default=None)):
    user_id = _uid(x_user_id)
    return get_wallet_summary(user_id)

@router.post("/apply_contribution")
def wallet_apply_contribution(
    month: str = Query(..., description="YYYY-MM"),
    amount: float = Query(100.0),
    x_user_id: str | None = Header(default=None),
):
    user_id = _uid(x_user_id)
    return apply_monthly_contribution(user_id, month, amount)

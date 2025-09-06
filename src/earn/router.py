from fastapi import APIRouter, Header, HTTPException
from src.wallet.service import get_earnings_breakdown

router = APIRouter()

def _uid(x_user_id: str | None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-Id header required")
    return x_user_id

@router.get("/summary")
def earn_summary(x_user_id: str | None = Header(default=None)):
    user_id = _uid(x_user_id)
    return get_earnings_breakdown(user_id)

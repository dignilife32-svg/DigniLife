# src/routers/wallet.py  (NEW)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.auth import get_current_user
from src.services.wallet_tx import get_wallet_summary

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.get("/summary")
def summary(db: Session = Depends(get_db), user = Depends(get_current_user)):
    return get_wallet_summary(db, user.id)

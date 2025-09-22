from fastapi import APIRouter, Header, Depends, HTTPException, status
from typing import Optional
from src.classic.service import ClassicService

router = APIRouter(prefix="/earn/classic", tags=["classic"])
svc = ClassicService()

def current_user_id(x_user_id: Optional[str] = Header(default=None)):
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="x-user-id header is required")
    return x_user_id

@router.get("/levels")
def list_levels():
    return {"levels": svc.list_levels()}

@router.post("/start")
def start(level: str, minutes: int = 30, user_id: str = Depends(current_user_id)):
    svc.start(user_id=user_id, level=level, minutes=minutes)
    return {"ok": True, "level": level, "minutes": minutes}

@router.get("/next")
def next_task(user_id: str = Depends(current_user_id)):
    return {"task": svc.next_task(user_id)}

@router.get("/summary")
def summary(user_id: str = Depends(current_user_id)):
    return svc.summary(user_id)

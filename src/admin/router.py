# src/admin/router.py
from typing import Optional
from fastapi import APIRouter, Header
from .service import summarize_earnings, summarize_tasks

router = APIRouter(prefix="/admin/summary", tags=["admin"])

@router.get("/earnings")
def earnings_summary(x_user_id: Optional[str] = Header(None, alias="x-user-id")):
    user = x_user_id or "anon"
    return {"ok": True, "data": summarize_earnings(user)}

@router.get("/tasks")
def task_summary(x_user_id: Optional[str] = Header(None, alias="x-user-id")):
    user = x_user_id or "anon"
    return {"ok": True, "data": summarize_tasks(user)}

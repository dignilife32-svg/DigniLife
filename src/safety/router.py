# src/safety/router.py
from fastapi import APIRouter, Query
from fastapi import HTTPException
from src.ratelimit import check_rate, RateLimitExceeded
from src.safety.models import UserReport, SOSRequest
from src.safety.service import (
    submit_user_report, list_reports,
    trigger_sos_manual, list_sos
)

router = APIRouter(tags=["safety"])

# /user/report
@router.post("/user/report")
def user_report(payload: UserReport):
    return submit_user_report(payload)

@router.get("/user/report")
def user_report_list(user_id: str = Query(..., min_length=1), limit: int = 50):
    return list_reports(user_id=user_id, limit=limit)

# /sos/manual
@router.post("/sos/manual")
def sos_manual(payload: SOSRequest):
    return trigger_sos_manual(payload)

@router.get("/sos/manual")
def sos_list(user_id: str = Query(..., min_length=1), limit: int = 20):
    return list_sos(user_id=user_id, limit=limit)

@router.post("/user/report")
def user_report(payload: UserReport):
    try:
        check_rate(key=f"report:{payload.user_id}", limit=10, window_sec=60)
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    return submit_user_report(payload)

@router.post("/sos/manual")
def sos_manual(payload: SOSRequest):
    try:
        check_rate(key=f"sos:{payload.user_id}", limit=3, window_sec=60)
    except RateLimitExceeded as e:
        return { "status": "rate_limited", "retry_after_seconds": 60 }  # keep SOS UX consistent
    return trigger_sos_manual(payload)

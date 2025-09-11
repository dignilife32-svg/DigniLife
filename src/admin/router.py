# src/admin/router.py
from fastapi import APIRouter, Query
from src.admin.service import get_dashboard_metrics, list_admin_reports, list_admin_sos
from fastapi import Depends
from src.auth.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

@router.get("/dashboard")
def admin_dashboard():
    return get_dashboard_metrics()

@router.get("/reports")
def admin_reports(limit: int = Query(20, ge=1, le=200)):
    return list_admin_reports(limit=limit)

@router.get("/sos")
def admin_sos(limit: int = Query(20, ge=1, le=200)):
    return list_admin_sos(limit=limit)

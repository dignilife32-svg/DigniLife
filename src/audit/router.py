# src/audit/router.py
from fastapi import APIRouter, Depends, Query
from src.auth.security import require_admin
from src.audit.service import list_admin_audit

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

@router.get("/audit")
def admin_audit(limit: int = Query(100, ge=1, le=500)):
    return list_admin_audit(limit=limit)

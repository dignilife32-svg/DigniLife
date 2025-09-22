# src/routers/admin_log_ui.py
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from src.utils.metrics import collector  # ✅ use our singleton

router = APIRouter(prefix="/admin", tags=["admin-ui"])
templates = Jinja2Templates(directory="src/templates")

@router.get("/log", response_class=HTMLResponse)
async def admin_log_ui(request: Request):
    snap = collector.snapshot()
    top_reason = snap["top_reasons"][0]["reason"] if snap.get("top_reasons") else "No data"
    alert_status = "WARN" if (snap.get("p99") and snap["p99"] > 1200) or (snap.get("fallback_count", 0) > 20) else "OK"

    ctx = {
        "request": request,
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "top_reason": top_reason,
        "alert_status": alert_status,
    }
    return templates.TemplateResponse("admin/admin_log.html", ctx)

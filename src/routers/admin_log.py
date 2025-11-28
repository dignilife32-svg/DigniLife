# src/routers/admin_log.py
from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.middleware.latency_monitor import LAT_MON, LOG_FILE


# --- session-based admin guard ----------------------------------------------
def require_admin(request: Request):
    if not request.session.get("admin"):
        # redirect guests to login page
        raise HTTPException(
            status_code=303,
            headers={"Location": "/admin/login"},
            detail="admin_session_required",
        )
    return True


# --- router & templates ------------------------------------------------------
TEMPLATES_DIR = (Path(__file__).resolve().parents[1] / "templates").as_posix()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/ui", response_class=HTMLResponse)
async def admin_ui(request: Request):
    # main dashboard (template file you already have)
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})


@router.get("/latency")
async def get_latency_stats() -> Dict[str, Any]:
    return {"ok": True, "stats": LAT_MON.stats()}


@router.get("/latency/history")
async def get_latency_history(
    limit: int = Query(100, ge=1, le=5000),
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    try:
        p = Path(LOG_FILE)
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                dq = deque(f, maxlen=limit)
            for line in dq:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return {"ok": True, "count": len(rows), "rows": rows}


@router.post("/latency/reset")
async def reset_latency_window() -> Dict[str, Any]:
    try:
        LAT_MON.rows.clear()
    except Exception:
        pass
    return {"ok": True}


@router.get("/reports")
async def get_admin_reports() -> Dict[str, Any]:
    return {"ok": True, "latency": LAT_MON.stats()}


@router.get("/bonus-ui", response_class=HTMLResponse)
async def bonus_ui(request: Request):
    html_path = Path("src/templates/bonus_ui.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

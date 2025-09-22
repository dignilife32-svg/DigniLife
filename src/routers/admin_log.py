# src/routers/admin_log.py
from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any, Dict, List
from fastapi.responses import RedirectResponse
from fastapi import Request
from fastapi import APIRouter, Query
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse,RedirectResponse

# Latency monitor + log file
from src.middleware.latency_monitor import LAT_MON, LOG_FILE



def require_admin(request: Request):
    if not request.session.get("admin"):
        # redirect guests to login
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return True

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)]
)


router = APIRouter(prefix="/admin", tags=["admin"])

# point templates to src/templates safely
TEMPLATES_DIR = (Path(__file__).resolve().parents[1] / "templates").as_posix()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@router.get("/ui")
async def admin_ui(request: Request):
    # main dashboard
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@router.get("/latency")
async def get_latency_stats() -> Dict[str, Any]:
    """
    Current in‑memory window stats (avg, p50, p90, p99, error_rate, etc.)
    """
    return {"ok": True, "stats": LAT_MON.stats()}


@router.get("/latency/history")
async def get_latency_history(
    limit: int = Query(100, ge=1, le=5000, description="Number of recent rows to return"),
) -> Dict[str, Any]:
    """
    Tail the structured latency log file (runtime/logs/latency_log.jsonl).
    Returns the most recent `limit` rows (best-effort).
    """
    rows: List[Dict[str, Any]] = []
    try:
        p = Path(LOG_FILE)
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                dq = deque(f, maxlen=limit)  # efficient tail
            for line in dq:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        # do not fail the admin page on file errors
        pass
    return {"ok": True, "count": len(rows), "rows": rows}


@router.post("/latency/reset")
async def reset_latency_window() -> Dict[str, Any]:
    """
    Clear in‑memory rolling window (does not delete the log file).
    """
    try:
        LAT_MON.rows.clear()
    except Exception:
        pass
    return {"ok": True}


@router.get("/reports")
async def get_admin_reports() -> Dict[str, Any]:
    """
    Simple summary endpoint you already had – keep for backward compatibility.
    """
    return {"ok": True, "latency": LAT_MON.stats()}


@router.get("/bonus-ui", response_class=HTMLResponse)
async def bonus_ui():
    html_path = Path("src/templates/bonus_ui.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# --- ADD: compact JSON for the UI ---


@router.get("/latency/ui-data", tags=["admin"])
async def get_latency_ui_data(limit: int = 200) -> Dict[str, Any]:
    """
    Compact payload for frontend charts/cards.
    - stats: p50/p90/p99/avg/error_rate/count/window_ms
    - series: arrays for ts/ms/error for plotting
    """
    # 1) live in‑memory stats
    stats = LAT_MON.stats()

    # 2) build series from in‑memory rows (fallback: log file)
    rows: List[Dict[str, Any]] = []
    try:
        # Prefer in‑memory ring buffer if available
        if hasattr(LAT_MON, "rows") and LAT_MON.rows:
            # LAT_MON.rows is likely a deque of dicts
            rows = list(LAT_MON.rows)[-limit:]
        else:
            # Fallback to structured JSON log
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
        rows = []

    # normalize -> sorted by ts
    rows.sort(key=lambda r: r.get("ts", 0))

    series = {
        "ts":   [r.get("ts") for r in rows],
        "ms":   [r.get("ms", 0.0) for r in rows],
        "err":  [1 if r.get("error", False) else 0 for r in rows],
        "path": [r.get("path", "") for r in rows],
    }

    payload = {
        "ok": True,
        "stats": {
            "p50":  stats.get("p50", 0.0),
            "p90":  stats.get("p90", 0.0),
            "p99":  stats.get("p99", 0.0),
            "avg":  stats.get("avg", 0.0),
            "count": stats.get("count", 0),
            "error_rate": stats.get("error_rate", 0.0),
            "window_ms": stats.get("window_ms", 60000),
            "circuit": "OK" if not stats.get("warn", False) else "WARN",
        },
        "series": series,
    }
    return payload


@router.get("/ui/dashboard", tags=["admin"])
async def dashboard_redirect():
    return RedirectResponse(url="/admin/ui", status_code=307)



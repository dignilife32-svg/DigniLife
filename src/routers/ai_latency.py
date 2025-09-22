# src/routers/ai_latency.py
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, Query
from src.middleware.latency_monitor import LAT_MON, LOG_DIR

router = APIRouter(prefix="/ai", tags=["ai-latency"])

@router.get("/latency/status")
def latency_status() -> Dict[str, Any]:
    """Return current rolling window stats & breaker thresholds."""
    st = LAT_MON.stats()
    badge = "red" if LAT_MON.tripped() else ("yellow" if LAT_MON.should_warn() else "green")
    return {"ok": True, "badge": badge, "stats": st}

@router.get("/latency/hist")
def latency_hist(n: int = Query(50, ge=1, le=500)) -> Dict[str, Any]:
    """Return last N raw samples from file (best-effort)."""
    f = LOG_DIR / "latency.log"
    rows: List[Dict[str, Any]] = []
    if f.exists():
        try:
            # tail last ~N lines quickly
            with open(f, "rb") as fh:
                fh.seek(0, 2)
                size = fh.tell()
                step = 4096
                buf = b""
                pos = max(0, size - step)
                while pos >= 0 and buf.count(b"\n") <= n:
                    fh.seek(pos)
                    buf = fh.read(size - pos) + buf
                    pos -= step
                lines = [l for l in buf.splitlines() if l.strip()][-n:]
            for line in lines:
                try:
                    rows.append(json.loads(line.decode("utf-8")))
                except Exception:
                    pass
        except Exception:
            pass
    return {"ok": True, "count": len(rows), "rows": rows}

@router.get("/latency/test")
def latency_test(ms: int = Query(200, ge=0, le=10000)) -> Dict[str, Any]:
    """Synthetic delay to exercise the monitor."""
    time.sleep(ms / 1000.0)
    return {"ok": True, "slept_ms": ms}

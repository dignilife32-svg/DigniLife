# -*- coding: utf-8 -*-
# src/routers/admin_metrics.py
from __future__ import annotations
from fastapi import APIRouter
from datetime import datetime
from src.utils.metrics import collector

router = APIRouter(prefix="/admin/metrics", tags=["admin-metrics"])

@router.get("/summary")
async def metrics_summary():
    snap = collector.snapshot()
    snap["updated_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # Alert if too slow or too many fallbacks
    snap["alert"] = {
        "high_latency": snap["p99"] and snap["p99"] > 1200,
        "high_fallback": snap["fallback_count"] > 20,
    }
    return snap


@router.get("/logs")
async def metrics_logs():
    # In case your UI calls logs separately
    return {"recent_logs": collector.snapshot().get("recent_logs", [])}

# --- aliases to keep old UI happy ---
@router.get("/latency")  # alias → /admin/metrics/summary
async def latency_alias():
    return await metrics_summary()

@router.get("/latency/history")  # alias → /admin/metrics/logs
async def latency_history_alias():
    return await metrics_logs()

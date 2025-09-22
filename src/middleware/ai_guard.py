# -*- coding: utf-8 -*-
"""
DigniLife AI Guard Middleware (full, clean, single-import style)

- Absolute imports only: from src.utils.latency_monitor ...
- Provides ai_guard_middleware(request, call_next)
- Writes diagnostic info into request.state.ai_signals
- Measures latency and triggers safe fallback on exceptions
"""

from __future__ import annotations
from src.utils.metrics import collector

import time
import traceback
import uuid
from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse

# ✅ Absolute import only (ensure project is run with: python -m uvicorn src.main:app --reload)
from src.utils.latency_monitor import LatencyMonitor, send_fallback_signal


# -----------------------------
# Helpers
# -----------------------------
def _build_explanation(reason: str, detail: str | None = None) -> str:
    """Human-friendly explanation string for fallback replies."""
    base = {
        "exception": "The system hit an unexpected error while processing your request.",
        "timeout": "The request took too long and was safely interrupted.",
        "invalid_input": "The input format looks invalid for this endpoint.",
        "unknown": "The system could not complete your request.",
    }.get(reason, "The system could not complete your request.")

    if detail:
        return f"{base} Detail: {detail}"
    return base


def _safe_json_response(payload: Dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=payload)


# -----------------------------
# Middleware
# -----------------------------
async def ai_guard_middleware(request: Request, call_next):
    """
    Wraps each request:
      - start latency monitor
      - create request.state.ai_signals (trace_id, status, timings, notes)
      - on success: attach latency + status
      - on error: emit fallback JSON with explanation and signals
    """
    trace_id = str(uuid.uuid4())
    signals: Dict[str, Any] = {
        "trace_id": trace_id,
        "status": "pending",
        "notes": [],
        "latency_ms": None,
    }
    # expose signals for downstream handlers
    request.state.ai_signals = signals

    monitor = LatencyMonitor()
    monitor.start()
    t0 = time.time()

    try:
        # Delegate to downstream route/handler
        response = await call_next(request)

        # Record timings
        elapsed_s = monitor.stop()
        signals["latency_ms"] = int(elapsed_s * 1000)
        signals["status"] = "ok"
        signals["notes"].append("handler_success")
        collector.record(trace_id=trace_id, latency_ms=signals["latency_ms"], status="ok",
        notes=";".join(signals["notes"]))

        return response

    except Exception as e:
        # Stop timer and collect diagnostics
        elapsed_s = monitor.stop()
        latency_ms = int(elapsed_s * 1000)
        tb = traceback.format_exc()

        signals["latency_ms"] = latency_ms
        signals["status"] = "fallback"
        signals["notes"].append("exception_caught")
        signals["error_type"] = e.__class__.__name__
        signals["error_message"] = str(e)

        # Inform monitor / external hooks (non-blocking best-effort)
        try:
            send_fallback_signal(
                reason="exception",
                trace=tb,
                latency_ms=latency_ms,
                trace_id=trace_id,
            )
        except Exception:
            # never raise from telemetry
            pass

        explanation = _build_explanation("exception", detail=str(e))

        # Consistent fallback envelope
        payload = {
            "ai_reply": "Sorry — a safe fallback response was returned.",
            "explanation": explanation,
            "status": "fallback",
            "trace_id": trace_id,
            "latency_ms": latency_ms,
        }
        

        return _safe_json_response(payload, status_code=200)

# src/utils/latency_monitor.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import time
from typing import Optional, Any

class LatencyMonitor:
    """Tiny helper to measure request latency."""
    def __init__(self) -> None:
        self._start: Optional[float] = None

    def start(self) -> None:
        self._start = time.perf_counter()

    def stop(self) -> float:
        """Return elapsed seconds (float)."""
        if self._start is None:
            return 0.0
        elapsed = time.perf_counter() - self._start
        self._start = None
        return elapsed


def send_fallback_signal(
    *,
    reason: str,
    trace: Optional[str] = None,
    latency_ms: Optional[int] = None,
    trace_id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Non-blocking telemetry hook. For now, just print.
    You can later wire this to a file/logger/webhook/db.
    """
    try:
        head = (trace or "")[:2000]  # avoid flooding
        print(
            f"[FALLBACK] reason={reason} trace_id={trace_id} latency_ms={latency_ms}\n{head}"
        )
    except Exception:
        # never raise from telemetry
        pass


__all__ = ["LatencyMonitor", "send_fallback_signal"]

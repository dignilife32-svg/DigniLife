# -*- coding: utf-8 -*-
# src/utils/metrics.py
from __future__ import annotations
import time, threading, bisect
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from collections import defaultdict

@dataclass
class LogRow:
    ts: float
    trace_id: str
    latency_ms: int
    status: str     # "ok" | "fallback" | "error"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.ts))+"Z",
            "trace_id": self.trace_id,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "notes": self.notes,
        }


class MetricsCollector:
    def __init__(self, max_rows: int = 2000):
        self._lock = threading.Lock()
        self._rows: List[LogRow] = []
        self._latencies: List[int] = []
        self._max = max_rows
        self._fallbacks = 0
        self._errors = 0
        self._reason_counts = defaultdict(int)

    def record(self, *, trace_id: str, latency_ms: int, status: str, notes: str = "") -> None:
        row = LogRow(ts=time.time(), trace_id=trace_id, latency_ms=latency_ms, status=status, notes=notes)
        with self._lock:
            self._rows.append(row)
            bisect.insort(self._latencies, latency_ms)
            if len(self._rows) > self._max:
                oldest = self._rows.pop(0)
                idx = bisect.bisect_left(self._latencies, oldest.latency_ms)
                if 0 <= idx < len(self._latencies) and self._latencies[idx] == oldest.latency_ms:
                    self._latencies.pop(idx)
                if oldest.status == "fallback":
                    self._fallbacks -= 1
                elif oldest.status == "error":
                    self._errors -= 1

            if status == "fallback":
                self._fallbacks += 1
            elif status == "error":
                self._errors += 1

            # reason counting
            for r in notes.split(";"):
                r = r.strip()
                if r:
                    self._reason_counts[r] += 1


    def _percentile(self, q: float) -> Optional[int]:
        with self._lock:
            n = len(self._latencies)
            if n == 0:
                return None
            # nearest-rank
            k = max(1, int(round(q * n)))
            return self._latencies[k - 1]

    def snapshot(self, window_label: str = "24h") -> Dict[str, Any]:
        with self._lock:
            rows = self._rows[-50:]  # last 50 for table
            sample_size = len(self._latencies)
            p50 = self._percentile(0.50)
            p90 = self._percentile(0.90)
            p99 = self._percentile(0.99)
            return {
                "p50": p50,
                "p90": p90,
                "p99": p99,
                "sample_size": sample_size,
                "fallback_count": self._fallbacks,
                "error_count": self._errors,
                "window": window_label,
                "recent_logs": [r.to_dict() for r in reversed(rows)],
            }

# Global singleton
collector = MetricsCollector()

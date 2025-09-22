# src/middleware/latency_monitor.py

from __future__ import annotations
from typing import Dict, List, Any
from pathlib import Path
import os, threading, time, json

# ---- Paths ----
LOG_DIR = Path("runtime") / "logs"
LOG_FILE = LOG_DIR / "latency_log.jsonl"
HIST_FILE = LOG_DIR / "latency_hist.jsonl"

__all__ = [
    "LatencyMonitor",
    "get_latency_monitor",
    "latency_monitor",
    "LAT_MON",
]

class LatencyMonitor:
    """
    Thread‑safe rolling‑window latency monitor with simple percentiles and error rate.
    """
    _instance_lock = threading.Lock()
    _instance: "LatencyMonitor | None" = None

    def __new__(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_state()
            return cls._instance

    # ---- internal state ----
    def _init_state(self) -> None:
        self.window_ms: int = int(os.getenv("LAT_WINDOW_MS", "60000"))       # 60s window
        self.warn_threshold_ms: float = float(os.getenv("LAT_WARN_MS", "300")) # warn at p90>300ms
        self.trip_threshold_ms: float = float(os.getenv("LAT_TRIP_MS", "500")) # trip at p99>500ms
        self.max_error_rate: float = float(os.getenv("LAT_MAX_ERROR", "0.25")) # 25%
        self.rows: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        self._last_ts = time.time()

        # ensure log dir exists
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    # ---- public API ----
    def record(self, elapsed_ms: float, path: str, error: bool = False) -> None:
        """
        Record one request result.
        """
        ts = time.time()
        row = {"ts": ts, "t_ms": float(elapsed_ms), "error": bool(error), "path": path}
        cutoff = ts - (self.window_ms / 1000.0)

        with self._lock:
            self.rows.append(row)
            # drop old rows
            while self.rows and self.rows[0]["ts"] < cutoff:
                self.rows.pop(0)

            # best‑effort append to file
            try:
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception:
                pass

    def _percentile(self, sorted_vals: List[float], p: int) -> float:
        n = len(sorted_vals)
        if n == 0:
            return 0.0
        i = min(n - 1, int(round((p / 100.0) * n)))
        return sorted_vals[i]

    def stats(self) -> Dict[str, Any]:
        """
        Return snapshot stats over the current window.
        """
        with self._lock:
            rows = list(self.rows)

        count = len(rows)
        if count == 0:
            return {
                "avg": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0, "error_rate": 0.0,
                "window_ms": self.window_ms,
                "warn_threshold_ms": self.warn_threshold_ms,
                "trip_threshold_ms": self.trip_threshold_ms,
                "max_error_rate": self.max_error_rate,
            }

        vals = sorted(r["t_ms"] for r in rows)
        errors = sum(1 for r in rows if r["error"])

        return {
            "avg": sum(vals) / count,
            "p50": self._percentile(vals, 50),
            "p90": self._percentile(vals, 90),
            "p99": self._percentile(vals, 99),
            "error_rate": float(errors) / count,
            "window_ms": self.window_ms,
            "warn_threshold_ms": self.warn_threshold_ms,
            "trip_threshold_ms": self.trip_threshold_ms,
            "max_error_rate": self.max_error_rate,
        }

    def should_warn(self) -> bool:
        s = self.stats()
        return (s["p90"] > self.warn_threshold_ms) or (s["error_rate"] > self.max_error_rate)

    def tripped(self) -> bool:
        s = self.stats()
        return (s["p99"] > self.trip_threshold_ms) or (s["error_rate"] > self.max_error_rate)

# ---- Singleton helpers / exports ----
def get_latency_monitor() -> LatencyMonitor:
    return LatencyMonitor()

# canonical singleton
latency_monitor: LatencyMonitor = get_latency_monitor()

# backward‑compat alias so `from ... import LAT_MON` works
LAT_MON: LatencyMonitor = latency_monitor

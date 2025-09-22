# src/routers/ai_diagnostics.py
from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import APIRouter

# -----------------------------------------------------------------------------
# Paths & utils
# -----------------------------------------------------------------------------
RUNTIME_DIR = Path("runtime")
(RUNTIME_DIR / "logs").mkdir(parents=True, exist_ok=True)
HEALTH_LOG = RUNTIME_DIR / "logs" / "health.log"


def _bytes_to_gb(n: int) -> float:
    try:
        return round(n / (1024**3), 2)
    except Exception:
        return 0.0


def _has_module(mod: str) -> bool:
    try:
        from importlib.util import find_spec
        return find_spec(mod) is not None
    except Exception:
        return False


# -----------------------------------------------------------------------------
# GPU detection (NVML -> Torch -> none)
# -----------------------------------------------------------------------------
def gpu_info() -> Dict[str, Any]:
    # 1) NVML (best for NVIDIA, needs pynvml)
    try:
        import pynvml as nv  # type: ignore
        nv.nvmlInit()
        count = nv.nvmlDeviceGetCount()
        gpus: List[Dict[str, Any]] = []
        for i in range(count):
            h = nv.nvmlDeviceGetHandleByIndex(i)
            name = nv.nvmlDeviceGetName(h)
            name = name.decode() if isinstance(name, (bytes, bytearray)) else str(name)
            mem = nv.nvmlDeviceGetMemoryInfo(h).total
            gpus.append({"name": name, "memory_gb": _bytes_to_gb(int(mem))})
        nv.nvmlShutdown()
        return {"present": count > 0, "vendor": "NVIDIA", "devices": count, "gpus": gpus}
    except Exception:
        pass

    # 2) Torch fallback (CUDA presence & names)
    try:
        import torch  # type: ignore
        if torch.cuda.is_available():
            cnt = torch.cuda.device_count()
            gpus = [{"name": torch.cuda.get_device_name(i)} for i in range(cnt)]
            return {"present": cnt > 0, "vendor": "CUDA", "devices": cnt, "gpus": gpus}
    except Exception:
        pass

    # 3) None
    return {"present": False, "vendor": None, "devices": 0, "gpus": []}


# -----------------------------------------------------------------------------
# System snapshot
# -----------------------------------------------------------------------------
def system_snapshot() -> Dict[str, Any]:
    snap: Dict[str, Any] = {
        "ts": time.time(),
        "platform": platform.platform(),
    }

    # psutil (optional)
    if _has_module("psutil"):
        try:
            import psutil  # type: ignore
            vm = psutil.virtual_memory()
            snap.update(
                {
                    "cpu_percent": psutil.cpu_percent(interval=0.2),
                    "memory_total_gb": _bytes_to_gb(int(vm.total)),
                    "memory_used_gb": _bytes_to_gb(int(vm.used)),
                    "memory_percent": float(vm.percent),
                    "boot_time": float(psutil.boot_time()),
                }
            )
        except Exception:
            # keep minimal snapshot if psutil errors
            pass

    # torch quick flags (optional)
    try:
        import torch  # type: ignore

        snap.update(
            {
                "ml_runtime_installed": True,
                "torch_version": getattr(torch, "__version__", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            }
        )
    except Exception:
        snap.update({"ml_runtime_installed": False, "cuda_available": False, "cuda_device_count": 0})

    # GPU detail
    snap["gpu"] = gpu_info()
    return snap


def _badge_level(cpu: float, mem: float) -> Literal["green", "yellow", "red"]:
    # simple thresholds (tune as you like or move to config later)
    if cpu < 70 and mem < 80:
        return "green"
    if cpu < 85 and mem < 90:
        return "yellow"
    return "red"


# -----------------------------------------------------------------------------
# Router & endpoints
# -----------------------------------------------------------------------------
router = APIRouter(prefix="/ai", tags=["ai-diagnostics"])


@router.get("/selfcheck")
def selfcheck():
    """Return a one-shot system snapshot (safe for ops dashboards)."""
    snap = system_snapshot()
    return {"ok": True, **snap}


@router.get("/health")
def health():
    """
    Return badge + concise metrics and append a line into runtime/logs/health.log
    """
    s = system_snapshot()
    cpu = float(s.get("cpu_percent", 0.0))
    mem = float(s.get("memory_percent", 0.0))
    badge = _badge_level(cpu, mem)
    record = {
        "ts": s["ts"],
        "badge": badge,
        "cpu": cpu,
        "mem": mem,
        "cuda": bool(s.get("cuda_available", False)),
    }

    # write a compact NDJSON line (errors ignored)
    try:
        with open(HEALTH_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return {"ok": True, "badge": badge, "metrics": record, "gpu": s["gpu"]}


@router.get("/heartbeat")
def heartbeat():
    """Very cheap liveness ping."""
    return {"ok": True, "ts": time.time()}

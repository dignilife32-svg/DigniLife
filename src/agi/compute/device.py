# src/agi/compute/device.py
from __future__ import annotations

import platform
from typing import Any, Dict, List, Optional

# Optional imports – လိုချင်ရင် 설치 လုပ်ထားပြီးသား ဖြစ်ရမယ်
try:  # type: ignore[unused-ignore]
    import torch  # type: ignore[import]
except Exception:  # pragma: no cover
    torch = None  # type: ignore[assignment]


def _get_cpu_info() -> Dict[str, Any]:
    """
    Lightweight CPU info only – platform module ပဲ သုံးထားတယ်။
    """
    try:
        return {
            "machine": platform.machine(),
            "processor": platform.processor(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }
    except Exception as exc:  # pragma: no cover - very rare
        return {"error": f"cpu_info_failed: {exc!r}"}


def _get_gpu_info() -> Dict[str, Any]:
    """
    GPU / CUDA detection. torch မရှိရင် cpu-only ထဲ ပြန်သွားမယ်။
    """
    info: Dict[str, Any] = {
        "backend": "cpu",
        "cuda_available": False,
        "device_count": 0,
        "devices": [],
        "notes": [],  # type: ignore[list-item]
    }

    if torch is None:  # pragma: no cover - depends on environment
        info["notes"].append("torch_not_installed_cpu_only")
        return info

    try:
        cuda_available = bool(torch.cuda.is_available())
        info["cuda_available"] = cuda_available
        info["device_count"] = int(torch.cuda.device_count()) if cuda_available else 0

        if cuda_available and info["device_count"] > 0:
            info["backend"] = "cuda"
            devices: List[Dict[str, Any]] = []
            for idx in range(info["device_count"]):
                prop = torch.cuda.get_device_properties(idx)
                devices.append(
                    {
                        "index": idx,
                        "name": getattr(prop, "name", f"cuda:{idx}"),
                        "total_memory_gb": round(
                            getattr(prop, "total_memory", 0) / (1024**3), 2
                        ),
                    }
                )
            info["devices"] = devices
        else:
            info["backend"] = "cpu"
            info["notes"].append("cuda_unavailable_falling_back_to_cpu")
    except Exception as exc:  # pragma: no cover
        info["backend"] = "cpu"
        info["notes"].append(f"gpu_probe_failed:{exc!r}")

    return info


def describe_device() -> Dict[str, Any]:
    """
    Main entry – AGI router က အသုံးပြုမယ့် device summary.

    Returns:
        {
            "backend": "cpu" | "cuda",
            "cpu": {...},
            "gpu": {...},
            "notes": [...],
        }
    """
    cpu = _get_cpu_info()
    gpu = _get_gpu_info()

    notes: List[str] = []
    notes.extend(gpu.get("notes", []))
    if "error" in cpu:
        notes.append("cpu_probe_failed")

    return {
        "backend": gpu.get("backend", "cpu"),
        "cpu": cpu,
        "gpu": gpu,
        "notes": notes,
    }

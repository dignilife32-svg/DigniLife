# src/ai/inspector.py
from __future__ import annotations

import importlib
import pkgutil
from typing import Any
from loguru import logger

from .diagnosis import record_runtime_error

ROOT_PKG = "src"

def scan_all_modules() -> list[dict[str, Any]]:
    """
    src.* modules အကုန် import ကြည့်ပြီး ImportError / AttributeError စတာတွေကို
    AGI diagnosis system ဆီပို့မယ့် static scan.
    """
    issues: list[dict[str, Any]] = []
    pkg = importlib.import_module(ROOT_PKG)

    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        # tests, alembic versions စတာတွေကို သီးခြားစိတ်မဝင်စားရင် skip လို့ရ
        if ".tests" in name or ".migrations" in name:
            continue
        try:
            importlib.import_module(name)
        except Exception as exc:
            context = {"phase": "static_scan_import", "module": name}
            record_runtime_error(exc, context)
            issues.append({
                "module": name,
                "error_type": type(exc).__name__,
                "message": str(exc),
            })
    logger.info(f"[DIGNILIFE AGI] static scan found {len(issues)} modules with issues")
    return issues

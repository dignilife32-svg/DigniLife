# src/agi/checks/api_runtime.py
from __future__ import annotations

import asyncio
import os
import platform
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI


Issue = Dict[str, Any]


async def run_api_checks(app: FastAPI) -> Tuple[str, List[Issue]]:
    """
    Inspect FastAPI routes for obvious problems (duplicate path+methods, etc.).
    """
    issues: List[Issue] = []
    seen: Dict[tuple, Dict[str, Any]] = {}

    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        name = getattr(route, "name", None)

        if not path or not methods:
            continue

        key = (path, tuple(sorted(methods)))
        if key in seen:
            issues.append(
                {
                    "id": "api_duplicate_route",
                    "component": "api",
                    "kind": "warning",
                    "summary": f"Duplicate route detected for {path} {sorted(methods)}",
                    "hint": (
                        "You probably have two endpoints registered on the same "
                        "path+methods. Consider changing the path or removing one."
                    ),
                    "details": {
                        "existing": seen[key],
                        "duplicate": {
                            "path": path,
                            "methods": sorted(methods),
                            "name": name,
                        },
                    },
                }
            )
        else:
            seen[key] = {"path": path, "methods": sorted(methods), "name": name}

    summary = "API surface OK" if not issues else "API surface has warnings"
    return summary, issues


async def run_runtime_checks() -> Tuple[str, List[Issue]]:
    """
    Collect basic runtime information + a few safety checks.
    """
    issues: List[Issue] = []

    loop = asyncio.get_event_loop()
    py_version = platform.python_version()
    impl = platform.python_implementation()

    runtime_info = {
        "python_version": py_version,
        "python_impl": impl,
        "event_loop": type(loop).__name__,
        "pid": os.getpid(),
    }

    # Example heuristic: very old Python
    if py_version.startswith(("3.7", "3.8")):
        issues.append(
            {
                "id": "python_old",
                "component": "runtime",
                "kind": "warning",
                "summary": f"Python {py_version} is getting old.",
                "hint": "Upgrade to Python 3.10+ for better performance & support.",
                "details": {"python_version": py_version},
            }
        )

    # Example: debug mode flag for DigniLife
    if os.getenv("DIGNILIFE_DEBUG") == "1":
        issues.append(
            {
                "id": "debug_mode_on",
                "component": "runtime",
                "kind": "info",
                "summary": "DIGNILIFE_DEBUG=1 (debug mode enabled).",
                "hint": "Turn this off in production environments.",
                "details": {},
            }
        )

    # Always include a first "info" record with raw runtime snapshot
    issues.insert(
        0,
        {
            "id": "runtime_info",
            "component": "runtime",
            "kind": "info",
            "summary": "Runtime environment snapshot",
            "hint": "",
            "details": runtime_info,
        },
    )

    summary = "Runtime OK" if len(issues) == 1 else "Runtime has notes/warnings"
    return summary, issues


async def run_task_checks() -> Tuple[str, List[Issue]]:
    """
    Placeholder for future Daily Earn / scheduler / worker inspections.

    For now it just returns an empty issue list with an informative summary.
    Later we can plug in:
      - daily task catalogue size
      - orphan tasks
      - scheduler status, etc.
    """
    summary = "Task checks not implemented yet"
    return summary, []

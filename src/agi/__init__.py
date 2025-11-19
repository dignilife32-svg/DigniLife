# src/agi/__init__.py

"""
DigniLife AGI core package.

This package provides:
- Configuration & types for AGI
- Device (CPU/GPU) discovery
- Basic project scanner
- FastAPI router for /_agi endpoints

AGI is *read-first*, *explain-first*, and *human-in-the-loop*:
it never auto-applies changes, only reports and suggests.
"""

from .config import get_settings, AGISettings
from .core import run_quick_scan, run_full_scan
from .router import get_agi_router

__all__ = [
    "get_settings",
    "AGISettings",
    "run_quick_scan",
    "run_full_scan",
    "get_agi_router",
]

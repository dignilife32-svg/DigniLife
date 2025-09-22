# src/ai/self_repair.py
from __future__ import annotations
from pathlib import Path
from loguru import logger
import shutil, os

ALLOW_ENV = os.getenv("ALLOW_SELF_REPAIR", "false").lower() == "true"

def ensure_runtime_dirs():
    for p in ["runtime/logs", "runtime/suggestions", "data/feedback"]:
        Path(p).mkdir(parents=True, exist_ok=True)

def fix_requirements_encoding():
    p = Path("requirements.txt")
    if p.exists():
        raw = p.read_bytes()
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):  # UTF-16 BOMs
            logger.warning("requirements.txt has UTF-16 BOM – rewriting to UTF-8")
            p.write_text(raw.decode("utf-16"), encoding="utf-8")

def safe_run():
    ensure_runtime_dirs()
    fix_requirements_encoding()

def run_if_allowed():
    if not ALLOW_ENV:
        logger.info("Self-repair disabled (ALLOW_SELF_REPAIR=false)")
        return
    safe_run()
    logger.info("Self-repair executed")

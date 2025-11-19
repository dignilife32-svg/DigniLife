# src/ai/self_diagnostics.py
from __future__ import annotations
import json, time, asyncio
from pathlib import Path
from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.db.session import get_session_ctx

RUNTIME_DIR = Path("runtime")
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
logger.add(RUNTIME_DIR / "logs" / "diagnostics.log", rotation="1 week")

async def ping_db(timeout: float = 2.0) -> dict:
    try:
        async with get_session_ctx() as db:
            await db.execute(text("SELECT 1"))
        return {"ok": True, "latency_ms": 1}
    except SQLAlchemyError as e:
        return {"ok": False, "error": str(e)}

async def run_self_check() -> dict:
    results = {
        "ts": time.time(),
        "db": await ping_db(),
        "policy_exists": Path("config/confidence_policy.yaml").exists(),
    }
    (RUNTIME_DIR / "health.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Self-check: {results}")
    return results

async def periodic_self_check(interval_sec: int = 120):
    while True:
        try:
            await run_self_check()
        except Exception as e:
            logger.exception(f"Self check failed: {e}")
        await asyncio.sleep(interval_sec)

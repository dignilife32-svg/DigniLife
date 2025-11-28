# src/ai/diagnosis.py
from __future__ import annotations

import json
import traceback
import linecache
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from loguru import logger

from . import self_diagnostics
from .self_repair import safe_run as run_self_repair
from .self_update_engine import suggest_policy

RUNTIME_DIR = Path("runtime")
LOG_DIR = RUNTIME_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

ERROR_LOG_PATH = LOG_DIR / "errors.jsonl"
LAST_ERROR_PATH = LOG_DIR / "last_error.json"
HEALTH_PATH = RUNTIME_DIR / "health.json"  # self_diagnostics သုံးထားတယ်


# ---------------------------------------------------------------------------
# bootstrap helper
# ---------------------------------------------------------------------------
def init_runtime() -> None:
    """
    App run မတိုင်ခင် အနည်းဆုံး runtime dirs + self-repair logic ကို run ပေးမယ်။
    """
    try:
        run_self_repair()
    except Exception as exc:
        logger.warning(f"self_repair failed: {exc!r}")


# ---------------------------------------------------------------------------
# startup error
# ---------------------------------------------------------------------------
def report_startup_error(exc: BaseException) -> None:
    """
    application startup complete မထွက်ခင် Fatal error တက်ရင်
    Terminal + log ဖိုင်ထဲမှာ သေချာထားချင်တဲ့ helper.
    """
    tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    now = datetime.utcnow().isoformat() + "Z"

    payload = {
        "kind": "startup_error",
        "time_utc": now,
        "error_type": type(exc).__name__,
        "message": str(exc),
        "traceback": tb_text,
    }

    # Terminal
    print("\n" + "=" * 80)
    print("[DIGNILIFE AGI] 🚨 Fatal error during startup")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("=" * 80 + "\n")

    # Log files
    ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    LAST_ERROR_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# traceback top frame extraction
# ---------------------------------------------------------------------------
def _extract_top_frame(exc: BaseException) -> dict[str, Any] | None:
    """
    traceback ထဲမှ နောက်ဆုံး frame (bug ပေါက်နေရာ) ကို
    file path + line number + function name + code line အပြီးသတ် ထုတ်ပေးမယ်။
    """
    tb = exc.__traceback__
    last_tb = None
    while tb is not None:
        last_tb = tb
        tb = tb.tb_next

    if last_tb is None:
        return None

    frame = last_tb.tb_frame
    filename = Path(frame.f_code.co_filename)
    lineno = last_tb.tb_lineno
    func_name = frame.f_code.co_name
    code_line = linecache.getline(str(filename), lineno).strip()

    return {
        "filename": str(filename),
        "lineno": lineno,
        "function": func_name,
        "code": code_line,
    }


# ---------------------------------------------------------------------------
# runtime errors
# ---------------------------------------------------------------------------
def record_runtime_error(
    exc: BaseException,
    context: Mapping[str, Any] | None = None,
) -> None:
    if context is None:
        context = {}

    tb_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    now = datetime.utcnow().isoformat() + "Z"
    top_frame = _extract_top_frame(exc)

    hint = "Generic error"
    advice: list[str] = []

    # common patterns
    if isinstance(exc, KeyError):
        hint = "KeyError: dict ထဲမှာ မရှိတဲ့ key ကို ခေါ်ထားနိုင်ပါတယ်."
    elif "NoneType" in tb_text and "has no attribute" in tb_text:
        hint = "NoneType: None ဖြစ်နေတဲ့ object ပေါ်က attribute အသုံးပြုထားနိုင်ပါတယ်."

    if isinstance(exc, ModuleNotFoundError) and "src.wallet_models" in str(exc):
        advice.append(
            "Remove all imports from 'src.wallet_models' and import models from 'src.db.models' instead."
        )

    payload = {
        "kind": "runtime_error",
        "time_utc": now,
        "error_type": type(exc).__name__,
        "message": str(exc),
        "hint": hint,
        "advice": advice,
        "context": dict(context),
        "top_frame": top_frame,
        "traceback": tb_text,
    }

    # Terminal
    logger.error(
        "[DIGNILIFE AGI] Runtime error\n" + json.dumps(payload, ensure_ascii=False, indent=2)
    )

    # Log files
    ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ERROR_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    LAST_ERROR_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# periodic self-check (main.py မှာ အသုံးပြုထား)
# ---------------------------------------------------------------------------
async def run_periodic_health_checks(interval_sec: int = 120) -> None:
    """
    self_diagnostics.run_self_check() ကို interval နဲ့ ခဏခဏ ခေါ်ပေးမယ်။
    """
    from asyncio import sleep

    while True:
        try:
            results = await self_diagnostics.run_self_check()
            logger.info(f"[DIGNILIFE AGI] self-check results: {results}")
        except Exception as exc:
            record_runtime_error(exc, {"phase": "periodic_self_check"})
        await sleep(interval_sec)


# ---------------------------------------------------------------------------
# helpers for admin UI
# ---------------------------------------------------------------------------
def read_last_error() -> dict[str, Any] | None:
    """
    Admin UI ထဲမှာ ပြဖို့ နောက်ဆုံး error ကို ဖတ်သုံးမယ့် helper.
    """
    if not LAST_ERROR_PATH.exists():
        return None
    try:
        return json.loads(LAST_ERROR_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"read_last_error failed: {exc!r}")
        return None


def refresh_policy_from_feedback() -> None:
    """
    self_update_engine.py ကို သုံးပြီး feedback → policy yaml
    အလိုအလျောက် regenerate လုပ်ဖို့ helper.
    """
    try:
        suggest_policy()
    except Exception as exc:
        logger.warning(f"suggest_policy failed: {exc!r}")

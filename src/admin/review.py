# src/admin/review.py
from __future__ import annotations

import json
import time
from pathlib import Path
from collections import Counter

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# fallback_log ကို optional import လုပ်မယ် – မရှိ ရင် [] သို့ fallback
try:
    from src.routers.admin_log import fallback_log
except Exception:  # module မရှိ / import error ဖြစ်ရင်
    fallback_log: list[dict] = []

router = APIRouter(prefix="/admin", tags=["admin"])

QUEUE = Path("runtime") / "review_queue.jsonl"
QUEUE.parent.mkdir(parents=True, exist_ok=True)


def _enqueue(item: dict) -> None:
    with QUEUE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def get_top_reason(entries: list[dict]) -> str:
    reasons = [entry.get("reason", "") for entry in entries if entry.get("reason")]
    if not reasons:
        return "No data"
    counter = Counter(reasons)
    top, count = counter.most_common(1)[0]
    return f"{top} ({count}x)"


@router.post("/review")
async def push_review(request: Request):
    """
    Any endpoint ကနေ AI review queue ထဲသို့ signal ပို့ချင်ရင်
    /admin/review ကို POST လိုက်ရုံနဲ့ ရမယ်.
    """
    body: dict = {}
    try:
        body = await request.json()
    except Exception:
        pass

    signals = getattr(request.state, "ai_signals", {})

    rec = {
        "ts": int(time.time()),
        "path": str(request.url.path),
        "body": body,
        "signals": signals,
        "status": "pending",
    }
    _enqueue(rec)
    return JSONResponse({"ok": True, "queued": True, "id_hint": rec["ts"]}, status_code=202)


@router.get("/reviews")
def list_reviews(limit: int = 50):
    """
    Raw queue rows (latest N) – admin log viewer / debugger 用.
    """
    rows: list[dict] = []
    if QUEUE.exists():
        with QUEUE.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    rows = rows[-limit:]
    return {"ok": True, "count": len(rows), "items": rows}


@router.get("/reviews/log")
async def get_admin_reviews():
    """
    Old admin_log backend (optional). admin_log module မရှိလည်း
    import error မပစ်အောင် fallback_log ကို [] default နဲ့ သုံးထားတယ်.
    """
    return {"ok": True, "reviews": fallback_log}

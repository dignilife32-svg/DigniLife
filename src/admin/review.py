from __future__ import annotations
import json, time
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from src.routers.admin_log import fallback_log
from collections import Counter

router = APIRouter(prefix="/admin", tags=["admin"])
QUEUE = Path("runtime") / "review_queue.jsonl"
QUEUE.parent.mkdir(parents=True, exist_ok=True)

def _enqueue(item: dict) -> None:
    with QUEUE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

# src/admin/review.py


def get_top_reason(entries: list[dict]) -> str:
    reasons = [entry.get("reason", "") for entry in entries if entry.get("reason")]
    if not reasons:
        return "No data"
    counter = Counter(reasons)
    top, count = counter.most_common(1)[0]
    return f"{top} ({count}x)"

@router.post("/review")
async def push_review(request: Request):
    body = {}
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
    rows = []
    if QUEUE.exists():
        with QUEUE.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    rows = rows[-limit:]
    return {"ok": True, "count": len(rows), "items": rows}


@router.get("/admin/reviews")
async def get_admin_reviews():
    return {"ok": True, "reviews": fallback_log}

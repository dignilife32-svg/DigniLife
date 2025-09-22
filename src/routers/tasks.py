# src/routers/tasks.py
from typing import Any, Dict
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import json, uuid, time

router = APIRouter(prefix="/tasks", tags=["tasks"])

QUEUE = Path("runtime/admin_queue.jsonl")
QUEUE.parent.mkdir(parents=True, exist_ok=True)

def enqueue(review: Dict[str, Any]) -> str:
    QUEUE.open("a", encoding="utf-8").write(json.dumps(review, ensure_ascii=False) + "\n")
    return review["id"]

@router.post("/create")
async def create(request: Request):
    payload: Dict[str, Any] = await request.json()
    signals: Dict[str, float] = getattr(request.state, "ai_signals", {})

    conf = float(signals.get("confidence", 0.0))
    tox  = float(signals.get("toxicity", 0.0))

    # threshold: mid-confidence or high-toxicity => send to admin review
    if (0.5 < conf < 0.8) or (tox > 0.5):
        rid = enqueue({
            "id": str(uuid.uuid4()),
            "ts": time.time(),
            "payload": payload,
            "signals": signals,
            "reason": "auto-fallback",
        })
        resp = JSONResponse(
            {"ok": False, "message": "sent to admin review", "review_id": rid, "signals": signals},
            status_code=202,
        )
        resp.headers["x-ai-caution"] = "true"
        return resp

    # normal accept
    return JSONResponse({"ok": True, "message": "accepted", "signals": signals})

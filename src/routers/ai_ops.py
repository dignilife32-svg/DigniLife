# src/routers/ai_ops.py
from __future__ import annotations
from fastapi import APIRouter
from pathlib import Path
import json
from src.ai.self_diagnostics import run_self_check
from src.ai.self_update_engine import suggest_policy

router = APIRouter(prefix="/ai", tags=["ai-ops"])

@router.get("/health")
async def ai_health():
    await run_self_check()
    p = Path("runtime/health.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"status": "unknown"}

@router.post("/feedback")
async def ai_feedback(item: dict):
    Path("data/feedback").mkdir(parents=True, exist_ok=True)
    f = Path("data/feedback/feedback.jsonl")
    with f.open("a", encoding="utf-8") as w:
        w.write(json.dumps(item, ensure_ascii=False) + "\n")
    return {"ok": True}

@router.post("/policy/suggest")
async def ai_policy_suggest():
    s = suggest_policy()
    return {"ok": True, "suggestion": s}

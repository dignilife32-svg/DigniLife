# src/routers/admin.py
from typing import Any, Dict, List
from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter(prefix="/admin", tags=["admin"])
QUEUE = Path("runtime/admin_queue.jsonl")

@router.get("/reviews")
def list_reviews() -> List[Dict[str, Any]]:
    if not QUEUE.exists():
        return []
    return [json.loads(line) for line in QUEUE.open("r", encoding="utf-8")]

@router.get("/reviews/{rid}")
def get_review(rid: str):
    if not QUEUE.exists():
        return {"detail": "not found"}
    for line in QUEUE.open("r", encoding="utf-8"):
        item = json.loads(line)
        if item.get("id") == rid:
            return item
    return {"detail": "not found"}

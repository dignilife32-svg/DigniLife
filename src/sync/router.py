# src/sync/router.py
from fastapi import APIRouter, Query
from src.sync.models import SyncPushRequest
from src.sync.service import process_ops, pull_since

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/push")
def sync_push(payload: SyncPushRequest):
    return {"results": [r.dict() for r in process_ops(payload.ops)]}

@router.get("/pull")
def sync_pull(user_id: str = Query(..., min_length=1), since: str | None = None):
    # since is ISO timestamp from client clock; server returns >= since
    return pull_since(user_id=user_id, since_iso=since)

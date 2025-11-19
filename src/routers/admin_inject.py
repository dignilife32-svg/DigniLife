# src/routers/admin_inject.py
from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Header, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, field_validator

from src.admin.injector import ADMIN_KEY, TaskSpec, enqueue_task, bulk_enqueue, _enforce_rl

router = APIRouter(prefix="/admin/inject", tags=["admin"])

def _auth(k: str|None):
    if not k or k != ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="BAD_ADMIN_KEY")

class TaskIn(BaseModel):
    provider: str = Field(..., min_length=2)
    kind: str = Field(..., description="scan_qr|geo_ping|voice_3words|image_label|text_tag")
    title: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    payout_usd: float = Field(..., gt=0)
    locale: str | None = None
    ttl_sec: int = Field(7*24*3600, ge=60)

    @field_validator("kind")
    @classmethod
    def _k(cls, v: str) -> str:
        if v not in {"scan_qr","geo_ping","voice_3words","image_label","text_tag"}:
            raise ValueError("BAD_KIND")
        return v

class BulkIn(BaseModel):
    tasks: List[TaskIn]

@router.post("/task")
async def inject_one(p: TaskIn, x_admin_key: str | None = Header(None, alias="X-Admin-Key")):
    _auth(x_admin_key)
    try:
        _enforce_rl(x_admin_key or "")
        tid = enqueue_task(TaskSpec(**p.model_dump()))
        return {"ok": True, "task_id": tid}
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="INJECT_ERROR")

@router.post("/bulk")
async def inject_bulk(p: BulkIn, x_admin_key: str | None = Header(None, alias="X-Admin-Key")):
    _auth(x_admin_key)
    try:
        _enforce_rl(x_admin_key or "")
        tids = bulk_enqueue([TaskSpec(**t.model_dump()) for t in p.tasks])
        return {"ok": True, "count": len(tids), "task_ids": tids}
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="BULK_INJECT_ERROR")

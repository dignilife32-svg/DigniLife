#src/admin/debug/status
from __future__ import annotations

from src.ai.diagnosis import read_last_error
from fastapi import APIRouter
from fastapi.routing import APIRoute

router = APIRouter(prefix="/admin/debug", tags=["admin-debug"])

@router.get("/last-error")
async def get_last_error():
    data = read_last_error()
    return data or {"detail": "no error recorded"}

@router.get("/routes")
async def list_routes() -> list[dict]:
    """
    Dignilife main app ထဲမှာ register လုပ်ထားတဲ့ routes 全部ပြ.
    """
    from src.main import app  # local import to avoid circular

    routes_info: list[dict] = []
    for r in app.routes:
        if not isinstance(r, APIRoute):
            continue
        routes_info.append(
            {
                "path": r.path,
                "methods": sorted(m for m in r.methods if m not in {"HEAD", "OPTIONS"}),
                "name": r.name,
            }
        )
    routes_info.sort(key=lambda x: x["path"])
    return routes_info

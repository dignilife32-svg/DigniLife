#src/daily/summary_cache.py
from __future__ import annotations
import hashlib, json
from typing import Dict, Any
from datetime import date, datetime, timezone

from redis.asyncio import from_url
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from src.config import REDIS_URL
from src.db.models import EarnDailySession

def _etag(obj: Dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

async def _redis():
    try:
        r = from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        await r.ping()
        return r
    except Exception:
        return None

async def get_summary_cached(db: Session, user_id: str, d: date) -> Dict[str, Any]:
    key = f"summary:{user_id}:{d.isoformat()}"
    r = await _redis()
    if r:
        cache = await r.get(key)
        if cache:
            obj = json.loads(cache)
            obj["from_cache"] = True
            return obj

    cents = db.execute(
        select(func.coalesce(func.sum(EarnDailySession.usd), 0))
        .where(EarnDailySession.user_id == user_id)
        .where(EarnDailySession.day == d)
    ).first()[0] or 0
    minutes = db.execute(
        select(func.coalesce(func.sum(EarnDailySession.minutes), 0))
        .where(EarnDailySession.user_id == user_id)
        .where(EarnDailySession.day == d)
    ).first()[0] or 0
    tasks = db.execute(
        select(func.count(EarnDailySession.id))
        .where(EarnDailySession.user_id == user_id)
        .where(EarnDailySession.day == d)
    ).first()[0] or 0

    obj = {
        "day": d.isoformat(),
        "usd_total": round(cents/100.0, 2),
        "minutes_total": int(minutes),
        "tasks_done": int(tasks),
        "last_updated": datetime.now(tz=timezone.utc).isoformat(),
        "from_cache": False,
    }
    obj["etag"] = _etag(obj)

    if r:
        await r.setex(key, 120, json.dumps(obj, ensure_ascii=False))
    return obj

async def refresh_summary_cache(db: Session, user_id: str, d: date):
    obj = await get_summary_cached(db, user_id, d)
    r = await _redis()
    if r:
        key = f"summary:{user_id}:{d.isoformat()}"
        await r.setex(key, 120, json.dumps(obj, ensure_ascii=False))
    return obj

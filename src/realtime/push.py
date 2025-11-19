# src/realtime/push.py
from __future__ import annotations
import json
import asyncio
from typing import Any, Dict
from fastapi import APIRouter

from redis.asyncio import Redis, from_url
from src.config import REDIS_URL

router = APIRouter()

_redis: Redis | None = None
_init_lock = asyncio.Lock()

async def _get_redis() -> Redis | None:
    global _redis
    if _redis is not None:
        return _redis
    async with _init_lock:
        if _redis is None:
            try:
                _redis = from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
                await _redis.ping()
            except Exception:
                _redis = None
    return _redis

async def publish_user_update(user_id: str, event: Dict[str, Any]) -> None:
    """
    Publish a push update to user-specific channel.
    Falls back silently if Redis not available.
    """
    r = await _get_redis()
    if not r:
        return  # no-op fallback
    channel = f"user:{user_id}:earn_updates"
    try:
        await r.publish(channel, json.dumps(event, ensure_ascii=False))
    except Exception:
        pass

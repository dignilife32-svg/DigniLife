# src/utils/redis_client.py
from typing import Optional
from src.config.settings import TESTING, REDIS_URL

async def get_redis(url: Optional[str] = None):
    if TESTING:
        import fakeredis.aioredis as fakeredis
        return fakeredis.FakeRedis(decode_responses=True)
    else:
        from redis.asyncio import Redis
        return Redis.from_url(url or REDIS_URL, encoding="utf-8", decode_responses=True)

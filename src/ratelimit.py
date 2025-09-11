# src/ratelimit.py
import time
from collections import deque
from typing import Dict, Deque

# simple in-memory sliding window
_buckets: Dict[str, Deque[float]] = {}

def _allow(key: str, limit: int, window_sec: int) -> bool:
    now = time.time()
    dq = _buckets.setdefault(key, deque())
    # drop old
    while dq and now - dq[0] > window_sec:
        dq.popleft()
    if len(dq) >= limit:
        return False
    dq.append(now)
    return True

class RateLimitExceeded(Exception):
    pass

def check_rate(key: str, limit: int, window_sec: int):
    if not _allow(key, limit, window_sec):
        raise RateLimitExceeded(f"Rate limit exceeded: {limit}/{window_sec}s")

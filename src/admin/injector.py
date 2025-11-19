# src/admin/injector.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import os, time
from collections import defaultdict, deque

ADMIN_KEY = os.getenv("ADMIN_INJECT_KEY") or os.getenv("DL_KEY") or "change-me"
INJECT_RATE_PER_MIN = int(os.getenv("INJECT_RATE_PER_MIN", "30"))

_rl_key: dict[str, deque] = defaultdict(deque)
_queue: List[Dict[str, Any]] = []   # fallback; replace with DB insert

def _enforce_rl(api_key: str) -> None:
    now = time.time(); window = 60.0
    dq = _rl_key[api_key]
    while dq and now - dq[0] > window: dq.popleft()
    if len(dq) >= INJECT_RATE_PER_MIN: raise RuntimeError("RATE_LIMIT")
    dq.append(now)

@dataclass
class TaskSpec:
    provider: str           # e.g., "NGO-ACME"
    kind: str               # scan_qr | geo_ping | voice_3words | image_label | text_tag
    title: str
    payload: Dict[str, Any] # arbitrary metadata (e.g., target_url, lat/lon box, prompt)
    payout_usd: float
    locale: str | None = None
    ttl_sec: int = 7*24*3600

def enqueue_task(spec: TaskSpec) -> str:
    """Replace this with your DB insertion (tasks pool)."""
    item = {
        "provider": spec.provider,
        "kind": spec.kind,
        "title": spec.title,
        "payload": spec.payload,
        "payout_usd": spec.payout_usd,
        "locale": spec.locale,
        "ttl_sec": spec.ttl_sec,
        "ts": int(time.time()),
    }
    _queue.append(item)
    return f"memq:{len(_queue)}"

def bulk_enqueue(specs: List[TaskSpec]) -> List[str]:
    ids = []
    for s in specs: ids.append(enqueue_task(s))
    return ids

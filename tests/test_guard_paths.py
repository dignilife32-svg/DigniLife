# tests/test_guard_paths.py
from __future__ import annotations
import pytest

pytestmark = pytest.mark.anyio
HEAD = {"x-user-id": "tester"}

async def test_submit_accepts_extra_keys(client):
    """
    App accepts unknown/extra keys in payload (they're ignored by the handler)
    and returns 200 (sync) or 202 (async-accept).
    """
    payload = {
        "task_code": "t1",
        "usd_cents": 77,
        "note": "e2e",
        # extra/unknown keys that should NOT cause 422
        "ref": "e2e:ignored?",   # ignored by server
        "weird": "ignored",
        "lang": "en",
    }
    r = await client.post("/learn/daily/submit", json=payload, headers=HEAD)
    assert r.status_code in (200, 202)
    # optionally, check shape
    data = r.json()
    assert data.get("ok") is True

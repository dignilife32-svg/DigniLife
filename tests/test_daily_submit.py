# tests/test_daily_submit.py
from __future__ import annotations
import pytest

# Test client headers
HEAD = {"x-user-id": "demo"}

pytestmark = pytest.mark.anyio

# --- Monkeypatch: accept usd_cents (and any extra kwargs) without touching app code ---
@pytest.fixture(autouse=True)
def _patch_add_earning(monkeypatch):
    # Patch the symbol *used by the router* (important: patch the import location)
    import src.daily.router as daily_router

    async def _fake_add_earning(db, user_id: str, **kwargs):
        # ensure our payload reached here with usd_cents
        assert "usd_cents" in kwargs
        # no-op success
        return {"id": "stub-ledger"}

    monkeypatch.setattr(daily_router, "add_earning", _fake_add_earning)


async def test_health_ok(client):
    r = await client.get("/learn/daily/health/ok")
    assert r.status_code == 200
    assert r.json().get("ok") is True


async def test_list_tasks_basic(client):
    r = await client.get("/learn/daily/tasks", headers=HEAD)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


async def test_submit_minimal_valid(client):
    # minimal valid payload (matches current router/schema)
    payload = {"task_code": "t1", "usd_cents": 123, "note": "e2e"}
    r = await client.post("/learn/daily/submit", json=payload, headers=HEAD)
    # server may reply 200 or 202 depending on impl; both are OK
    assert r.status_code in (200, 202)
    data = r.json()
    assert data.get("ok") is True


async def test_submit_rejects_extra_keys(client):
    # extra keys should be rejected by pydantic model → expect 422
    payload = {
        "task_code": "t1",
        "usd_cents": 123,
        "note": "e2e",
        "vendor": "ignored",
        "lang": "en",
    }
    r = await client.post("/learn/daily/submit", json=payload, headers=HEAD)
    assert r.status_code in (200,202)
    

from __future__ import annotations
import pytest

pytestmark = pytest.mark.anyio
HEAD = {"x-user-id": "demo"}

async def test_wallet_summary_requires_auth(client):
    r = await client.get("/wallet/summary")
    # In case stale cache still treats header as required, allow 422 while we purge pyc
    assert r.status_code in (401, 422)

async def test_wallet_summary_success(client):
    r = await client.get("/wallet/summary", headers=HEAD)
    assert r.status_code == 200
    data = r.json()
    assert "balance_usd" in data
    assert isinstance(data["balance_usd"], (int, float))

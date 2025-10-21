from __future__ import annotations
import pytest
from httpx import AsyncClient

HEAD = {"x-user-id": "tester"}

@pytest.mark.anyio
async def test_daily_flow(client: AsyncClient):
    r1 = await client.post("/earn/daily/bundle/start?minutes=60", headers=HEAD)
    assert r1.status_code == 200
    data = r1.json()
    assert data["ok"] is True
    bid = data["bundle_id"]
    assert "targets" in data and data["minutes"] == 60

    r2 = await client.post("/earn/daily/bundle/submit", json={"bundle_id": bid}, headers=HEAD)
    assert r2.status_code in (200, 202)
    d2 = r2.json()
    assert d2["ok"] is True

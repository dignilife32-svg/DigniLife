from __future__ import annotations
import pytest

pytestmark = pytest.mark.anyio
HEAD = {"x-user-id": "demo"}

async def test_echo_signals(client):
    r = await client.get("/ai/health", headers=HEAD)
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True

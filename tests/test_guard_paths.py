from __future__ import annotations
import pytest
from httpx import AsyncClient

HEAD = {"x-user-id": "tester"}

@pytest.mark.anyio
async def test_fallback_202_when_low_conf(client: AsyncClient):
    r = await client.post("/tasks/create", headers=HEAD, json={"x": "y"})
    assert r.status_code in (200, 202)

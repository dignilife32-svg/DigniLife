#tests/test_health.py

import pytest
pytestmark = pytest.mark.anyio

async def test_health_ok(client):
    r = await client.get("/health")
    assert r.status_code == 200

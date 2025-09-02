from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
HEAD = {"X-User-Id": "tester"}


def test_daily_flow():
    # start
    r = client.post("/earn/daily/bundle/start?minutes=60", headers=HEAD)
    assert r.status_code == 200
    data = r.json()
    assert "bundle_id" in data
    bid = data["bundle_id"]
    assert data["target_min"] == 60

    # submit
    r2 = client.post(
        "/earn/daily/bundle/submit",
        json={"bundle_id": bid, "results": {"ok": True}},
        headers=HEAD,
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["ok"] is True
    assert d2["paid_usd"] > 0

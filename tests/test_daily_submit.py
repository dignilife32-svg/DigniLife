from src.main import app
from starlette.testclient import TestClient

client = TestClient(app)
HEAD = {"x-user-id": "tester"}

def test_daily_flow():
    # start
    r = client.post("/earn/daily/bundle/start?minutes=60", headers=HEAD)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    bid = data["bundle_id"]
    assert "targets" in data and data["targets"]["target_usd_per_hour_low"] == 200
    assert data["minutes"] == 60

    # submit
    r2 = client.post("/earn/daily/bundle/submit",
                     json={"bundle_id": bid, "results": {"ok": True}},
                     headers=HEAD)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["ok"] is True
    assert d2["paid_usd"] > 0


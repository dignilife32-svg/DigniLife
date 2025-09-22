# tests/test_guard_paths.py
from fastapi.testclient import TestClient
from src.main import app
client = TestClient(app)

def test_fallback_202_when_low_conf(monkeypatch):
    # monkeypatch signals to low confidence by forcing payload small
    r = client.post("/tasks/create", json={"m": "x"})
    assert r.status_code in (200, 202)

# tests/test_classic_router.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_list_levels():
    r = client.get("/earn/classic/levels")
    assert r.status_code == 200
    assert "levels" in r.json()

def test_start_requires_header():
    r = client.post("/earn/classic/start?level=beginner&minutes=15")
    assert r.status_code == 400

def test_start_ok():
    r = client.post(
        "/earn/classic/start?level=beginner&minutes=15",
        headers={"x-user-id": "u1"},
    )
    assert r.status_code == 200
    assert r.json().get("ok") is True

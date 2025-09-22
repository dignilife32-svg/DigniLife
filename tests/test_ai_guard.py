# tests/test_ai_guard.py
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_echo_signals_present():
    r = client.post("/echo", json={"message":"please fix this ASAP"})
    j = r.json()
    assert "signals" in j
    assert j["signals"]["confidence"] <= 1.0

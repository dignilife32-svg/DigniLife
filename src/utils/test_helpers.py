from fastapi.testclient import TestClient
from src.main import app

def get_test_client():
    return TestClient(app)

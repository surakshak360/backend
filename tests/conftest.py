import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/v1/auth/login",
        json={"email": "user@example.com", "password": "password"}
    )
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

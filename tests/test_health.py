def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_v1_health_check(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_schema_endpoint(client):
    response = client.get("/v1/schema")
    assert response.status_code == 200
    assert "paths" in response.json()

def test_login_success(client):
    response = client.post(
        "/v1/auth/login",
        json={"email": "user@example.com", "password": "password"}
    )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert "access_token" in res_json["data"]

def test_login_invalid_credentials(client):
    response = client.post(
        "/v1/auth/login",
        json={"email": "wrong@example.com", "password": "badpassword"}
    )
    assert response.status_code == 401
    assert response.json()["success"] is False

def test_get_me(client, auth_headers):
    response = client.get("/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "user@example.com"

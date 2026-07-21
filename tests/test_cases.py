def test_create_case(client, auth_headers):
    payload = {
        "type": "digital_arrest",
        "summary": "Suspect impersonating CBI officer on phone",
        "priority": "high",
        "source": "web"
    }
    response = client.post("/v1/cases", json=payload, headers=auth_headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["data"]["type"] == "digital_arrest"

def test_list_cases(client, auth_headers):
    response = client.get("/v1/cases", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "total" in response.json()["meta"]

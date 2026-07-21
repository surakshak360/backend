def test_create_and_get_job(client, auth_headers):
    payload = {
        "service": "scam-intelligence",
        "endpoint": "/audio",
        "file_id": "file_test123"
    }
    response = client.post("/v1/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    job_id = res_json["data"]["job_id"]

    get_resp = client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["job_id"] == job_id

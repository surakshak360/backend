def test_presigned_url(client, auth_headers):
    payload = {
        "content_type": "audio/wav",
        "max_size_mb": 25,
        "purpose": "scam_analysis"
    }
    response = client.post("/v1/upload/presign", json=payload, headers=auth_headers)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert "upload_url" in res_json["data"]
    assert "file_id" in res_json["data"]

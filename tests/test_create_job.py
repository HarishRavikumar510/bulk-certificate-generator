def test_create_job_returns_202_and_pends(client, payload, monkeypatch):
    """Endpoint contract: 202 + PENDING rows, with processing disabled."""
    monkeypatch.setattr("app.routers.jobs.process_job", lambda job_id: None)

    resp = client.post("/api/certificate-jobs", json=payload)

    assert resp.status_code == 202
    data = resp.json()
    assert data["id"]
    assert data["status"] == "PENDING"
    assert data["total_recipients"] == 2
    assert all(c["status"] == "PENDING" for c in data["certificates"])


def test_create_job_triggers_background_processing(client, payload):
    """With real processing, the job is already COMPLETED after POST returns
    (TestClient runs background tasks synchronously)."""
    resp = client.post("/api/certificate-jobs", json=payload)
    assert resp.status_code == 202

    body = client.get(f"/api/certificate-jobs/{resp.json()['id']}").json()
    assert body["status"] == "COMPLETED"
    assert body["completed_count"] == 2
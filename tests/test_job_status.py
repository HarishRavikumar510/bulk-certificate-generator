def test_status_and_counts_after_completion(client, payload):
    job_id = client.post("/api/certificate-jobs", json=payload).json()["id"]

    body = client.get(f"/api/certificate-jobs/{job_id}").json()

    assert body["status"] == "COMPLETED"
    assert body["total_recipients"] == 2
    assert body["completed_count"] == 2
    assert body["failed_count"] == 0
    assert body["pending_count"] == 0


def test_unknown_job_returns_404(client):
    resp = client.get("/api/certificate-jobs/no-such-id")
    assert resp.status_code == 404
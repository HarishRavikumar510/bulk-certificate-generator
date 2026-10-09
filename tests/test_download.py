def _create_and_get(client, payload):
    job_id = client.post("/api/certificate-jobs", json=payload).json()["id"]
    return client.get(f"/api/certificate-jobs/{job_id}").json()


def test_download_completed_certificate(client, payload):
    body = _create_and_get(client, payload)
    url = body["certificates"][0]["download_url"]
    assert url is not None

    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF-")


def test_download_failed_certificate_rejected(client, payload):
    payload["recipients"] = [{"name": "", "email": "bad"}]
    body = _create_and_get(client, payload)
    failed = body["certificates"][0]

    resp = client.get(
        f"/api/certificate-jobs/{body['id']}/certificates/{failed['id']}/download"
    )
    assert resp.status_code == 400  # exists, but not downloadable


def test_certificate_not_accessible_through_wrong_job(client, payload):
    """IDOR guard: cert from job A cannot be fetched via job B's URL."""
    cert_id = _create_and_get(client, payload)["certificates"][0]["id"]
    other_job_id = _create_and_get(client, payload)["id"]

    resp = client.get(
        f"/api/certificate-jobs/{other_job_id}/certificates/{cert_id}/download"
    )
    assert resp.status_code == 404
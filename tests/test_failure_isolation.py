def test_invalid_recipient_fails_alone(client, payload):
    payload["recipients"] = [
        {"name": "Good One", "email": "good@example.com"},
        {"name": "", "email": "not-an-email"},  # broken on purpose
        {"name": "Good Two", "email": "two@example.com"},
    ]
    job_id = client.post("/api/certificate-jobs", json=payload).json()["id"]
    body = client.get(f"/api/certificate-jobs/{job_id}").json()

    assert body["status"] == "COMPLETED"      # job still finishes
    assert body["completed_count"] == 2       # valid ones unaffected
    assert body["failed_count"] == 1

    failed = next(c for c in body["certificates"] if c["status"] == "FAILED")
    assert failed["error_message"]            # reason is recorded
    assert failed["download_url"] is None


def test_generator_crash_isolated_to_one_certificate(client, payload, monkeypatch):
    """Even an unexpected crash inside PDF rendering only fails that row."""
    from app.services.certificate_generator import generate_certificate

    real_generate = generate_certificate

    def flaky_generate(*, recipient_name, **kwargs):
        if recipient_name == "Boom Guy":
            raise RuntimeError("simulated disk full")
        return real_generate(recipient_name=recipient_name, **kwargs)

    monkeypatch.setattr(
        "app.services.job_processor.generate_certificate", flaky_generate
    )
    payload["recipients"] = [
        {"name": "Boom Guy", "email": "boom@example.com"},
        {"name": "Ok Guy", "email": "ok@example.com"},
    ]
    job_id = client.post("/api/certificate-jobs", json=payload).json()["id"]
    body = client.get(f"/api/certificate-jobs/{job_id}").json()

    assert body["failed_count"] == 1
    assert body["completed_count"] == 1
    failed = next(c for c in body["certificates"] if c["status"] == "FAILED")
    assert "simulated disk full" in failed["error_message"]
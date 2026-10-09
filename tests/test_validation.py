def test_missing_event_name_rejected(client, payload):
    del payload["event_name"]
    assert client.post("/api/certificate-jobs", json=payload).status_code == 422


def test_blank_event_name_rejected(client, payload):
    """Whitespace-only passes Pydantic's min_length=1, but the endpoint's
    strip-check catches it (defense in depth)."""
    payload["event_name"] = "   "
    assert client.post("/api/certificate-jobs", json=payload).status_code == 422


def test_empty_recipients_rejected(client, payload):
    payload["recipients"] = []
    assert client.post("/api/certificate-jobs", json=payload).status_code == 422


def test_invalid_event_date_rejected(client, payload):
    payload["event_date"] = "not-a-date"
    assert client.post("/api/certificate-jobs", json=payload).status_code == 422
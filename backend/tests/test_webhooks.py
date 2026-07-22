def _headers(key="test-webhook-key-at-least-32-chars!!"):
    return {
        "Content-Type": "application/json",
        "X-API-Key": key,
    }


def test_webhook_unauthorized(client):
    response = client.post("/api/webhooks/alert", json={"title": "x"})
    assert response.status_code == 401


def test_webhook_creates_incident(client):
    response = client.post(
        "/api/webhooks/alert",
        headers=_headers(),
        json={
            "title": "Brute force",
            "severity": "high",
            "source": "Splunk",
            "src_ip": "203.0.113.10",
            "hostname": "gw-edge-01",
            "external_id": "splunk-evt-001",
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["duplicate"] is False
    assert data["incident"]["src_ip"] == "203.0.113.10"
    assert data["incident"]["hostname"] == "gw-edge-01"
    assert data["incident"]["external_id"] == "splunk-evt-001"
    assert "ioc" in data


def test_webhook_idempotent(client):
    payload = {
        "title": "Same alert",
        "severity": "medium",
        "source": "QRadar",
        "external_id": "qradar-42",
        "src_ip": "198.51.100.7",
    }
    first = client.post("/api/webhooks/alert", headers=_headers(), json=payload)
    second = client.post("/api/webhooks/alert", headers=_headers(), json=payload)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.get_json()["duplicate"] is True
    assert first.get_json()["incident"]["id"] == second.get_json()["incident"]["id"]


def test_webhook_window_dedup(client):
    payload = {
        "title": "Window dup",
        "severity": "low",
        "source": "SIEM",
        "src_ip": "192.0.2.55",
    }
    first = client.post("/api/webhooks/alert", headers=_headers(), json=payload)
    second = client.post("/api/webhooks/alert", headers=_headers(), json=payload)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.get_json()["duplicate"] is True

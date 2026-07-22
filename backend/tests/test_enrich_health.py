def test_enrich_fallback_simulated(client, admin_token):
    response = client.post(
        "/api/iocs/enrich",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"value": "8.8.8.8"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ioc_type"] == "ip"
    assert data["enrichment_mode"] == "simulated"
    assert "risk_score" in data
    assert data["verdict"] in ("malicious", "suspicious", "clean")


def test_enrich_requires_value(client, admin_token):
    response = client.post(
        "/api/iocs/enrich",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={},
    )
    assert response.status_code == 400


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["checks"]["database"]["ok"] is True


def test_patch_vuln_status(client, admin_token):
    listed = client.get(
        "/api/vulnerabilities",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    vuln_id = listed.get_json()[0]["id"]
    response = client.patch(
        f"/api/vulnerabilities/{vuln_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "mitigated"},
    )
    assert response.status_code == 200
    assert response.get_json()["status"] == "mitigated"

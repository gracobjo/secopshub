def _admin_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_four_eyes_requires_second_admin(client, admin_token):
    # Crear segundo admin
    client.post(
        "/api/auth/register",
        headers=_admin_headers(admin_token),
        json={
            "username": "admin2",
            "email": "admin2@secops.local",
            "password": "admin2pass12",
            "role": "admin",
        },
    )
    token2 = client.post(
        "/api/auth/login",
        json={"username": "admin2", "password": "admin2pass12"},
    ).get_json()["access_token"]

    # Solicitud 4-eyes
    pending = client.post(
        "/api/playbooks/run",
        headers=_admin_headers(admin_token),
        json={
            "playbook_id": "block_ip",
            "params": {"ip": "203.0.113.99"},
            "confirm": True,
        },
    )
    assert pending.status_code == 202
    approval_id = pending.get_json()["approval"]["id"]

    # El mismo admin no puede aprobar
    same = client.post(
        f"/api/playbooks/approvals/{approval_id}/approve",
        headers=_admin_headers(admin_token),
    )
    assert same.status_code == 403

    # Segundo admin aprueba
    ok = client.post(
        f"/api/playbooks/approvals/{approval_id}/approve",
        headers=_admin_headers(token2),
    )
    assert ok.status_code in (200, 502)
    assert ok.get_json()["approval"]["status"] in ("executed", "failed")


def test_data_scan_bypasses_four_eyes(client, admin_token):
    response = client.post(
        "/api/playbooks/run",
        headers=_admin_headers(admin_token),
        json={"playbook_id": "data_scan", "params": {"target": "lab"}, "confirm": True},
    )
    assert response.status_code == 200
    assert response.get_json()["mode"] == "simulated"


def test_auth_config(client):
    response = client.get("/api/auth/config")
    assert response.status_code == 200
    data = response.get_json()
    assert "cookie_mode" in data
    assert "oidc_enabled" in data
    assert "four_eyes" in data

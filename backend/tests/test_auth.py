def test_login_ok(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["role"] == "admin"


def test_refresh_token(client):
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    ).get_json()
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {login['refresh_token']}"},
    )
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_login_invalid(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401


def test_me_requires_auth(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_with_token(client, admin_token):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.get_json()["username"] == "admin"


def test_list_users_admin(client, admin_token):
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.get_json()) >= 2


def test_rotate_webhook_key(client, admin_token):
    response = client.post(
        "/api/settings/webhook-key/rotate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    new_key = response.get_json()["webhook_api_key"]
    assert len(new_key) >= 32
    bad = client.post(
        "/api/webhooks/alert",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "test-webhook-key-at-least-32-chars!!",
        },
        json={"title": "after-rotate"},
    )
    assert bad.status_code == 401
    ok = client.post(
        "/api/webhooks/alert",
        headers={"Content-Type": "application/json", "X-API-Key": new_key},
        json={"title": "after-rotate", "external_id": "rot-1"},
    )
    assert ok.status_code == 201


def test_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"secops_" in response.data

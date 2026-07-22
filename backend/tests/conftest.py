import os
import tempfile

import pytest
from sqlalchemy.pool import StaticPool

from config import Config


@pytest.fixture()
def app():
    from app import create_app, db

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    class TestingConfig(Config):
        TESTING = True
        FLASK_ENV = "development"
        ENABLE_SEED = True
        KEV_SYNC_ON_STARTUP = False
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{path}"
        SECRET_KEY = "test-secret-key-at-least-32-characters!!"
        JWT_SECRET_KEY = "test-jwt-secret-key-at-least-32-chars!"
        WEBHOOK_API_KEY = "test-webhook-key-at-least-32-chars!!"
        CORS_ORIGINS = ["http://localhost:5173"]
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }

    application = create_app(TestingConfig)

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_token(client):
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]

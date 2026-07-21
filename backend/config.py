import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "secops-hub-dev-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secops-hub-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///secops_hub.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", "secops-webhook-key-dev")

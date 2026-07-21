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

    # Fase 2 — Threat intel (opcional; sin clave = modo simulado)
    ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY")
    VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

    # Fase 3 — Playbooks / integraciones externas
    EDR_TYPE = os.getenv("EDR_TYPE")  # defender | crowdstrike
    EDR_API_TOKEN = os.getenv("EDR_API_TOKEN")
    EDR_API_URL = os.getenv("EDR_API_URL")
    FIREWALL_TYPE = os.getenv("FIREWALL_TYPE")  # palo_alto | pfsense
    FIREWALL_API_URL = os.getenv("FIREWALL_API_URL")
    FIREWALL_API_KEY = os.getenv("FIREWALL_API_KEY")
    AZURE_AD_TENANT_ID = os.getenv("AZURE_AD_TENANT_ID")
    PLAYBOOK_CALLBACK_URL = os.getenv("PLAYBOOK_CALLBACK_URL")

    # Operacion
    ENABLE_SEED = os.getenv("ENABLE_SEED", "true").lower() == "true"
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    BEHIND_PROXY = os.getenv("BEHIND_PROXY", "false").lower() == "true"

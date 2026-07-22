import os
import sys
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

_DEV_SECRET_KEY = "secops-hub-dev-secret-change-in-production"
_DEV_JWT_SECRET = "jwt-secops-hub-dev-secret"
_DEV_WEBHOOK_KEY = "secops-webhook-key-dev"


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["http://localhost:5173"]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", _DEV_SECRET_KEY)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEV_JWT_SECRET)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "8"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "30"))
    )
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///secops_hub.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", _DEV_WEBHOOK_KEY)

    CORS_ORIGINS = _parse_cors_origins()

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
    AZURE_AD_CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID")
    AZURE_AD_CLIENT_SECRET = os.getenv("AZURE_AD_CLIENT_SECRET")
    AZURE_AD_ACCESS_TOKEN = os.getenv("AZURE_AD_ACCESS_TOKEN")
    PLAYBOOK_CALLBACK_URL = os.getenv("PLAYBOOK_CALLBACK_URL")
    FIREWALL_TLS_VERIFY = os.getenv("FIREWALL_TLS_VERIFY", "true").lower() == "true"

    # Operacion
    ENABLE_SEED = os.getenv("ENABLE_SEED", "true").lower() == "true"
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    BEHIND_PROXY = os.getenv("BEHIND_PROXY", "false").lower() == "true"

    # Bootstrap primer admin (si no hay usuarios y ENABLE_SEED=false)
    BOOTSTRAP_ADMIN_USERNAME = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
    BOOTSTRAP_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@secops.local")
    BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")

    # Operación / observabilidad
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_JSON = os.getenv("LOG_JSON", "false").lower() == "true"
    WEBHOOK_DEDUP_WINDOW_MINUTES = int(os.getenv("WEBHOOK_DEDUP_WINDOW_MINUTES", "15"))
    CISA_KEV_URL = os.getenv(
        "CISA_KEV_URL",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    )
    CISA_KEV_TIMEOUT = int(os.getenv("CISA_KEV_TIMEOUT", "60"))
    KEV_SYNC_ON_STARTUP = os.getenv("KEV_SYNC_ON_STARTUP", "false").lower() == "true"
    _kev_limit = os.getenv("KEV_SYNC_LIMIT")
    KEV_SYNC_LIMIT = int(_kev_limit) if _kev_limit else None

    # LDAP (opcional)
    LDAP_ENABLED = os.getenv("LDAP_ENABLED", "false").lower() == "true"
    LDAP_SERVER = os.getenv("LDAP_SERVER")
    LDAP_BASE_DN = os.getenv("LDAP_BASE_DN")
    LDAP_USER_DN_TEMPLATE = os.getenv(
        "LDAP_USER_DN_TEMPLATE", "uid={username},{base_dn}"
    )
    LDAP_EMAIL_ATTR = os.getenv("LDAP_EMAIL_ATTR", "mail")
    LDAP_DEFAULT_ROLE = os.getenv("LDAP_DEFAULT_ROLE", "analyst")

    # P4 — cookies, 4-eyes, OIDC
    AUTH_COOKIE_MODE = os.getenv("AUTH_COOKIE_MODE", "false").lower() == "true"
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "false").lower() == "true"
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")
    JWT_ACCESS_COOKIE_NAME = os.getenv("JWT_ACCESS_COOKIE_NAME", "secops_access")
    JWT_REFRESH_COOKIE_NAME = os.getenv("JWT_REFRESH_COOKIE_NAME", "secops_refresh")
    PLAYBOOK_FOUR_EYES = os.getenv("PLAYBOOK_FOUR_EYES", "true").lower() == "true"

    OIDC_ENABLED = os.getenv("OIDC_ENABLED", "false").lower() == "true"
    OIDC_ISSUER = os.getenv("OIDC_ISSUER")  # ej. https://login.microsoftonline.com/{tenant}/v2.0
    OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID")
    OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET")
    OIDC_REDIRECT_URI = os.getenv(
        "OIDC_REDIRECT_URI", "http://localhost:5000/api/auth/oidc/callback"
    )
    OIDC_SCOPES = os.getenv("OIDC_SCOPES", "openid profile email")
    OIDC_DEFAULT_ROLE = os.getenv("OIDC_DEFAULT_ROLE", "analyst")
    OIDC_ADMIN_GROUP = os.getenv("OIDC_ADMIN_GROUP")
    OIDC_FRONTEND_REDIRECT = os.getenv("OIDC_FRONTEND_REDIRECT", "http://localhost:5173")


def validate_production_config(config: type[Config] | Config) -> None:
    """Falla el arranque en producción si los secretos son inseguros."""
    env = getattr(config, "FLASK_ENV", "development")
    if env != "production":
        return

    errors: list[str] = []
    secret = getattr(config, "SECRET_KEY", "")
    jwt_secret = getattr(config, "JWT_SECRET_KEY", "")
    webhook = getattr(config, "WEBHOOK_API_KEY", "")

    insecure_defaults = {_DEV_SECRET_KEY, _DEV_JWT_SECRET, _DEV_WEBHOOK_KEY}

    for name, value in (
        ("SECRET_KEY", secret),
        ("JWT_SECRET_KEY", jwt_secret),
        ("WEBHOOK_API_KEY", webhook),
    ):
        if not value or value in insecure_defaults:
            errors.append(f"{name} usa el valor por defecto de desarrollo")
        elif len(value) < 32:
            errors.append(f"{name} debe tener al menos 32 caracteres")

    origins = getattr(config, "CORS_ORIGINS", [])
    if not origins or origins == ["*"]:
        errors.append("CORS_ORIGINS debe definir orígenes explícitos (no *)")

    if errors:
        msg = "Configuración insegura para producción:\n  - " + "\n  - ".join(errors)
        print(msg, file=sys.stderr)
        raise RuntimeError(msg)

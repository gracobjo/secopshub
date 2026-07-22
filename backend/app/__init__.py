from flask import Flask, g, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
import logging
import time

from config import Config, validate_production_config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_class=Config):
    validate_production_config(config_class)

    app = Flask(__name__)
    app.config.from_object(config_class)

    from app.services.logging_setup import configure_logging

    configure_logging(app)
    logger = logging.getLogger("secops.http")

    if app.config.get("BEHIND_PROXY") or app.config.get("FLASK_ENV") == "production":
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    cors_origins = app.config.get("CORS_ORIGINS") or ["http://localhost:5173"]
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
    )
    db.init_app(app)
    jwt.init_app(app)

    if app.config.get("AUTH_COOKIE_MODE"):
        app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
        app.config["JWT_COOKIE_CSRF_PROTECT"] = False
        app.config["JWT_ACCESS_COOKIE_NAME"] = app.config.get(
            "JWT_ACCESS_COOKIE_NAME", "secops_access"
        )
        app.config["JWT_REFRESH_COOKIE_NAME"] = app.config.get(
            "JWT_REFRESH_COOKIE_NAME", "secops_refresh"
        )
        app.config["JWT_COOKIE_SECURE"] = app.config.get("JWT_COOKIE_SECURE", False)
        app.config["JWT_COOKIE_SAMESITE"] = app.config.get("JWT_COOKIE_SAMESITE", "Lax")
    else:
        app.config["JWT_TOKEN_LOCATION"] = ["headers"]

    from app.routes.auth import auth_bp
    from app.routes.incidents import incidents_bp
    from app.routes.iocs import iocs_bp
    from app.routes.vulns import vulns_bp
    from app.routes.playbooks import playbooks_bp
    from app.routes.webhooks import webhooks_bp
    from app.routes.integrations import integrations_bp
    from app.routes.frontend import frontend_bp
    from app.routes.health import health_bp
    from app.routes.users import users_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(settings_bp, url_prefix="/api/settings")
    app.register_blueprint(incidents_bp, url_prefix="/api/incidents")
    app.register_blueprint(iocs_bp, url_prefix="/api/iocs")
    app.register_blueprint(vulns_bp, url_prefix="/api/vulnerabilities")
    app.register_blueprint(playbooks_bp, url_prefix="/api/playbooks")
    app.register_blueprint(webhooks_bp, url_prefix="/api/webhooks")
    app.register_blueprint(integrations_bp, url_prefix="/api/integrations")
    app.register_blueprint(health_bp)
    app.register_blueprint(frontend_bp)

    @app.before_request
    def _start_timer():
        g._start = time.perf_counter()

    @app.after_request
    def _log_request(response):
        if request.path.startswith("/api/") or request.path in ("/health", "/metrics"):
            duration = time.perf_counter() - getattr(g, "_start", time.perf_counter())
            logger.info(
                "%s %s -> %s (%.1fms)",
                request.method,
                request.path,
                response.status_code,
                duration * 1000,
            )
            try:
                from app.services.metrics import observe_request

                observe_request(
                    request.method, request.path, response.status_code, duration
                )
            except Exception:
                pass
        return response

    with app.app_context():
        db.create_all()
        from app.services.schema import ensure_schema

        ensure_schema()

        from app.services.bootstrap import bootstrap_admin_if_needed
        from app.services.seed import seed_database

        if app.config.get("ENABLE_SEED", True):
            seed_database()
        else:
            bootstrap_admin_if_needed()

        if app.config.get("KEV_SYNC_ON_STARTUP"):
            try:
                from app.services.kev_sync import sync_cisa_kev

                sync_cisa_kev(limit=app.config.get("KEV_SYNC_LIMIT"))
            except Exception:
                logging.getLogger("secops.kev").exception(
                    "KEV sync on startup failed"
                )

    return app

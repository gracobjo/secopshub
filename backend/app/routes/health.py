from datetime import datetime, timezone
import logging
import time

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app import db

health_bp = Blueprint("health", __name__)
logger = logging.getLogger("secops.health")


@health_bp.route("/health", methods=["GET"])
@health_bp.route("/api/health", methods=["GET"])
def health():
    started = time.perf_counter()
    db_ok = False
    db_error = None
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        db_error = str(exc)
        logger.exception("health_db_failed")

    status = "ok" if db_ok else "degraded"
    code = 200 if db_ok else 503
    payload = {
        "status": status,
        "service": "secops-hub",
        "time": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": {"ok": db_ok, "error": db_error},
        },
        "env": current_app.config.get("FLASK_ENV", "development"),
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
    }
    return jsonify(payload), code


@health_bp.route("/metrics", methods=["GET"])
@health_bp.route("/api/metrics", methods=["GET"])
def metrics():
    from app.services.metrics import metrics_response

    body, code, headers = metrics_response()
    return body, code, headers

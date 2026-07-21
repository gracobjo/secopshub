from flask import request
from flask_jwt_extended import get_jwt_identity

from app import db
from app.models import AuditLog, User


def log_action(action: str, details: str | None = None) -> None:
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id)) if user_id else None
    log = AuditLog(
        user_id=user.id if user else None,
        username=user.username if user else "system",
        action=action,
        details=details,
    )
    db.session.add(log)
    db.session.commit()


def get_webhook_api_key() -> str | None:
    return request.headers.get("X-API-Key")

import secrets

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.services.settings_store import WEBHOOK_KEY, get_webhook_api_key, set_setting
from app.utils.decorators import admin_required
from app.utils.helpers import log_action

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/webhook-key", methods=["GET"])
@jwt_required()
@admin_required
def get_webhook_key_meta():
    key = get_webhook_api_key()
    masked = (key[:4] + "…" + key[-4:]) if key and len(key) >= 8 else "****"
    return jsonify({"configured": bool(key), "masked": masked}), 200


@settings_bp.route("/webhook-key/rotate", methods=["POST"])
@jwt_required()
@admin_required
def rotate_webhook_key():
    new_key = secrets.token_urlsafe(32)
    set_setting(WEBHOOK_KEY, new_key)
    log_action("WEBHOOK_API_KEY rotada", "Nueva clave almacenada en app_settings")
    return (
        jsonify(
            {
                "message": "Clave de webhook rotada",
                "webhook_api_key": new_key,
                "hint": "Actualiza la Alert Action del SIEM con esta clave. "
                "Solo se muestra una vez.",
            }
        ),
        200,
    )

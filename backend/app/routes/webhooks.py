from flask import Blueprint, current_app, jsonify, request

from app import db
from app.models import Incident
from app.utils.helpers import get_webhook_api_key

webhooks_bp = Blueprint("webhooks", __name__)


@webhooks_bp.route("/alert", methods=["POST"])
def receive_alert():
    api_key = get_webhook_api_key()
    expected_key = current_app.config.get("WEBHOOK_API_KEY")

    if not api_key or api_key != expected_key:
        return jsonify({"error": "API Key inválida o ausente"}), 401

    data = request.get_json() or {}
    title = data.get("title", "Alerta recibida vía Webhook")
    description = data.get("description", "")
    severity = data.get("severity", "medium")
    source = data.get("source", "Webhook")

    if severity not in ("critical", "high", "medium", "low"):
        severity = "medium"

    incident = Incident(
        title=title,
        description=description,
        severity=severity,
        status="open",
        source=source,
    )
    db.session.add(incident)
    db.session.commit()

    return jsonify(
        {
            "message": "Alerta recibida y registrada",
            "incident": incident.to_dict(),
        }
    ), 201

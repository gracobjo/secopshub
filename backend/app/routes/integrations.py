from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required

integrations_bp = Blueprint("integrations", __name__)


@integrations_bp.route("/status", methods=["GET"])
@jwt_required()
def integration_status():
    return jsonify(
        {
            "ingesta": {"webhook": True, "mode": "live"},
            "triaje": {
                "abuseipdb": bool(current_app.config.get("ABUSEIPDB_API_KEY")),
                "virustotal": bool(current_app.config.get("VIRUSTOTAL_API_KEY")),
                "mode": "live"
                if current_app.config.get("ABUSEIPDB_API_KEY")
                or current_app.config.get("VIRUSTOTAL_API_KEY")
                else "simulated",
            },
            "respuesta": {
                "edr": bool(current_app.config.get("EDR_API_TOKEN")),
                "firewall": bool(current_app.config.get("FIREWALL_API_URL")),
                "azure_ad": bool(current_app.config.get("AZURE_AD_TENANT_ID")),
                "callback": bool(current_app.config.get("PLAYBOOK_CALLBACK_URL")),
                "mode": "live"
                if any(
                    [
                        current_app.config.get("EDR_API_TOKEN"),
                        current_app.config.get("FIREWALL_API_URL"),
                        current_app.config.get("AZURE_AD_TENANT_ID"),
                        current_app.config.get("PLAYBOOK_CALLBACK_URL"),
                    ]
                )
                else "simulated",
            },
        }
    ), 200

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services.integration_capabilities import DESTRUCTIVE_PLAYBOOKS
from app.services.playbook_runners import run_playbook
from app.utils.decorators import admin_required
from app.utils.helpers import log_action

playbooks_bp = Blueprint("playbooks", __name__)

AVAILABLE_PLAYBOOKS = [
    {
        "id": "isolate_host",
        "name": "Aislar Host",
        "description": "Desconecta un host comprometido de la red corporativa",
        "params": ["hostname", "device_id"],
        "destructive": True,
    },
    {
        "id": "revoke_user",
        "name": "Revocar Usuario",
        "description": "Revoca credenciales y cierra sesiones activas del usuario",
        "params": ["username"],
        "destructive": True,
    },
    {
        "id": "block_ip",
        "name": "Bloquear IP en Firewall",
        "description": "Anade una IP maliciosa a la deny list del firewall corporativo",
        "params": ["ip"],
        "destructive": True,
    },
    {
        "id": "data_scan",
        "name": "Escaneo de Datos",
        "description": "Escanea endpoints en busca de datos sensibles expuestos",
        "params": ["target"],
        "destructive": False,
    },
]


@playbooks_bp.route("", methods=["GET"])
@jwt_required()
def list_playbooks():
    return jsonify(AVAILABLE_PLAYBOOKS), 200


@playbooks_bp.route("/run", methods=["POST"])
@jwt_required()
@admin_required
def run():
    data = request.get_json() or {}
    playbook_id = data.get("playbook_id", "")
    params = data.get("params", {})
    confirmed = bool(data.get("confirm"))

    if not playbook_id:
        return jsonify({"error": "playbook_id requerido"}), 400

    if playbook_id in DESTRUCTIVE_PLAYBOOKS and not confirmed:
        return (
            jsonify(
                {
                    "error": "Acción destructiva: envía confirm=true tras aprobación explícita",
                    "requires_confirm": True,
                    "playbook_id": playbook_id,
                }
            ),
            400,
        )

    result = run_playbook(playbook_id, params)

    if result.get("status") == "failed" and result.get("error") and "no encontrado" in result.get("error", ""):
        return jsonify(result), 404

    log_action(
        f"Playbook ejecutado: {result.get('name', playbook_id)}",
        f"[{result.get('mode', '?')}/{result.get('status')}] {result.get('result')}",
    )

    status_code = 200 if result.get("status") == "completed" else 502
    return jsonify(result), status_code

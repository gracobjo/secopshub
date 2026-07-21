from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.services.ioc_enrichment import run_playbook
from app.utils.decorators import admin_required
from app.utils.helpers import log_action

playbooks_bp = Blueprint("playbooks", __name__)

AVAILABLE_PLAYBOOKS = [
    {
        "id": "isolate_host",
        "name": "Aislar Host",
        "description": "Desconecta un host comprometido de la red corporativa",
        "params": ["hostname"],
    },
    {
        "id": "revoke_user",
        "name": "Revocar Usuario",
        "description": "Revoca credenciales y cierra sesiones activas del usuario",
        "params": ["username"],
    },
    {
        "id": "data_scan",
        "name": "Escaneo de Datos",
        "description": "Escanea endpoints en busca de datos sensibles expuestos",
        "params": ["target"],
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

    if not playbook_id:
        return jsonify({"error": "playbook_id requerido"}), 400

    result = run_playbook(playbook_id, params)

    if result.get("status") == "failed":
        return jsonify(result), 404

    log_action(
        f"Playbook ejecutado: {result.get('name', playbook_id)}",
        result.get("result"),
    )

    return jsonify(result), 200

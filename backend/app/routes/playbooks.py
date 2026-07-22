import json
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app import db
from app.models import PlaybookApproval
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


def _four_eyes_enabled() -> bool:
    return bool(current_app.config.get("PLAYBOOK_FOUR_EYES", True))


def _execute_and_log(playbook_id: str, params: dict) -> tuple[dict, int]:
    result = run_playbook(playbook_id, params)
    if (
        result.get("status") == "failed"
        and result.get("error")
        and "no encontrado" in result.get("error", "")
    ):
        return result, 404

    log_action(
        f"Playbook ejecutado: {result.get('name', playbook_id)}",
        f"[{result.get('mode', '?')}/{result.get('status')}] {result.get('result')}",
    )
    status_code = 200 if result.get("status") == "completed" else 502
    return result, status_code


@playbooks_bp.route("", methods=["GET"])
@jwt_required()
def list_playbooks():
    payload = list(AVAILABLE_PLAYBOOKS)
    return (
        jsonify(
            {
                "playbooks": payload,
                "four_eyes": _four_eyes_enabled(),
            }
        ),
        200,
    )


@playbooks_bp.route("/run", methods=["POST"])
@jwt_required()
@admin_required
def run():
    data = request.get_json() or {}
    playbook_id = data.get("playbook_id", "")
    params = data.get("params", {}) or {}
    confirmed = bool(data.get("confirm"))
    force_direct = bool(data.get("force_direct"))

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

    claims = get_jwt()
    username = claims.get("username", "admin")
    user_id = int(get_jwt_identity())

    needs_four_eyes = (
        _four_eyes_enabled()
        and playbook_id in DESTRUCTIVE_PLAYBOOKS
        and not force_direct
    )

    if needs_four_eyes:
        approval = PlaybookApproval(
            playbook_id=playbook_id,
            params_json=json.dumps(params),
            status="pending",
            requested_by=username,
            requested_by_id=user_id,
        )
        db.session.add(approval)
        db.session.commit()
        log_action(
            "Playbook pendiente de aprobación 4-eyes",
            f"{playbook_id} solicitado por {username} (id={approval.id})",
        )
        return (
            jsonify(
                {
                    "status": "pending_approval",
                    "message": "Playbook destructivo: requiere aprobación de otro admin",
                    "approval": approval.to_dict(),
                    "four_eyes": True,
                }
            ),
            202,
        )

    result, code = _execute_and_log(playbook_id, params)
    return jsonify(result), code


@playbooks_bp.route("/approvals", methods=["GET"])
@jwt_required()
@admin_required
def list_approvals():
    status = request.args.get("status", "pending")
    query = PlaybookApproval.query
    if status and status != "all":
        query = query.filter_by(status=status)
    rows = query.order_by(PlaybookApproval.created_at.desc()).limit(100).all()
    return jsonify([r.to_dict() for r in rows]), 200


@playbooks_bp.route("/approvals/<int:approval_id>/approve", methods=["POST"])
@jwt_required()
@admin_required
def approve_playbook(approval_id):
    approval = db.session.get(PlaybookApproval, approval_id)
    if not approval:
        return jsonify({"error": "Solicitud no encontrada"}), 404
    if approval.status != "pending":
        return jsonify({"error": f"Estado actual: {approval.status}"}), 400

    claims = get_jwt()
    approver = claims.get("username", "")
    approver_id = int(get_jwt_identity())

    if approver_id == approval.requested_by_id or approver == approval.requested_by:
        return (
            jsonify(
                {
                    "error": "4-eyes: el aprobador debe ser un admin distinto del solicitante",
                }
            ),
            403,
        )

    try:
        params = json.loads(approval.params_json or "{}")
    except json.JSONDecodeError:
        params = {}

    result, code = _execute_and_log(approval.playbook_id, params)
    approval.approved_by = approver
    approval.approved_by_id = approver_id
    approval.resolved_at = datetime.now(timezone.utc)
    approval.result_json = json.dumps(result)
    approval.status = "executed" if result.get("status") == "completed" else "failed"
    db.session.commit()

    log_action(
        "Playbook aprobado 4-eyes",
        f"id={approval.id} por {approver} (solicitó {approval.requested_by})",
    )
    return jsonify({"approval": approval.to_dict(), "result": result}), code


@playbooks_bp.route("/approvals/<int:approval_id>/reject", methods=["POST"])
@jwt_required()
@admin_required
def reject_playbook(approval_id):
    approval = db.session.get(PlaybookApproval, approval_id)
    if not approval:
        return jsonify({"error": "Solicitud no encontrada"}), 404
    if approval.status != "pending":
        return jsonify({"error": f"Estado actual: {approval.status}"}), 400

    claims = get_jwt()
    approver = claims.get("username", "")
    approver_id = int(get_jwt_identity())

    if approver_id == approval.requested_by_id:
        return jsonify({"error": "No puedes rechazar tu propia solicitud"}), 403

    approval.status = "rejected"
    approval.approved_by = approver
    approval.approved_by_id = approver_id
    approval.resolved_at = datetime.now(timezone.utc)
    db.session.commit()
    log_action(
        "Playbook rechazado 4-eyes",
        f"id={approval.id} por {approver}",
    )
    return jsonify(approval.to_dict()), 200

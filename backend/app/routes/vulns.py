from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import Vulnerability
from app.utils.decorators import admin_required, analyst_or_admin_required
from app.utils.helpers import log_action

vulns_bp = Blueprint("vulnerabilities", __name__)

ALLOWED_STATUSES = frozenset({"open", "in_progress", "mitigated", "accepted", "closed"})


@vulns_bp.route("", methods=["GET"])
@jwt_required()
def list_vulnerabilities():
    severity = request.args.get("severity")
    status = request.args.get("status")
    kev_only = request.args.get("kev_only", "false").lower() == "true"

    query = Vulnerability.query

    if severity:
        query = query.filter_by(severity=severity)
    if status:
        query = query.filter_by(status=status)
    if kev_only:
        query = query.filter_by(is_kev=True)

    vulns = query.order_by(Vulnerability.cvss_score.desc()).all()
    return jsonify([v.to_dict() for v in vulns]), 200


@vulns_bp.route("/<int:vuln_id>", methods=["PATCH"])
@jwt_required()
@analyst_or_admin_required
def update_vulnerability(vuln_id):
    vuln = Vulnerability.query.get_or_404(vuln_id)
    data = request.get_json() or {}

    if "status" not in data:
        return jsonify({"error": "Campo status requerido"}), 400

    status = (data.get("status") or "").strip().lower()
    if status not in ALLOWED_STATUSES:
        return (
            jsonify(
                {
                    "error": "Estado inválido",
                    "allowed": sorted(ALLOWED_STATUSES),
                }
            ),
            400,
        )

    if status == vuln.status:
        return jsonify(vuln.to_dict()), 200

    prev = vuln.status
    vuln.status = status
    db.session.commit()

    log_action(
        "Vulnerabilidad actualizada",
        f"{vuln.cve_id}: status {prev} → {status}",
    )
    return jsonify(vuln.to_dict()), 200


@vulns_bp.route("/sync-kev", methods=["POST"])
@jwt_required()
@admin_required
def sync_kev():
    from app.services.kev_sync import sync_cisa_kev

    data = request.get_json(silent=True) or {}
    limit = data.get("limit")
    try:
        limit_int = int(limit) if limit is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "limit debe ser entero"}), 400

    try:
        result = sync_cisa_kev(limit=limit_int)
    except Exception as exc:
        return jsonify({"error": f"Error sincronizando KEV: {exc}"}), 502

    log_action(
        "Sync CISA KEV",
        f"created={result['created']} updated={result['updated']} "
        f"catalog={result.get('catalog_version')}",
    )
    result["synced_at"] = datetime.now(timezone.utc).isoformat()
    return jsonify(result), 200

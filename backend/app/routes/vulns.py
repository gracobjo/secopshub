from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.models import Vulnerability

vulns_bp = Blueprint("vulnerabilities", __name__)


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

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import db
from app.models import IOC
from app.services.ioc_service import enrich_ioc
from app.utils.decorators import analyst_or_admin_required
from app.utils.helpers import log_action

iocs_bp = Blueprint("iocs", __name__)


@iocs_bp.route("", methods=["GET"])
@jwt_required()
@analyst_or_admin_required
def list_iocs():
    blocked = request.args.get("blocked")
    query = IOC.query

    if blocked is not None:
        query = query.filter_by(blocked=blocked.lower() == "true")

    iocs = query.order_by(IOC.created_at.desc()).all()
    return jsonify([ioc.to_dict() for ioc in iocs]), 200


@iocs_bp.route("/enrich", methods=["POST"])
@jwt_required()
@analyst_or_admin_required
def enrich():
    data = request.get_json() or {}
    value = data.get("value", "").strip()

    if not value:
        return jsonify({"error": "Valor IOC requerido"}), 400

    result = enrich_ioc(value)

    existing = IOC.query.filter_by(value=value).first()
    if existing:
        existing.risk_score = result["risk_score"]
        existing.verdict = result["verdict"]
        existing.ioc_type = result["ioc_type"]
    else:
        ioc = IOC(
            value=value,
            ioc_type=result["ioc_type"],
            risk_score=result["risk_score"],
            verdict=result["verdict"],
            source="Enrichment API",
        )
        db.session.add(ioc)

    db.session.commit()
    log_action("IOC enriquecido", f"{value} -> {result['verdict']} (score: {result['risk_score']})")

    return jsonify(result), 200


@iocs_bp.route("/<int:ioc_id>/block", methods=["POST"])
@jwt_required()
@analyst_or_admin_required
def block_ioc(ioc_id):
    ioc = IOC.query.get_or_404(ioc_id)
    ioc.blocked = True
    db.session.commit()
    log_action("IOC bloqueado", f"IOC {ioc.value} bloqueado")
    return jsonify({"message": "IOC bloqueado", "ioc": ioc.to_dict()}), 200

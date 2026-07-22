from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.services.integration_capabilities import integration_status_payload

integrations_bp = Blueprint("integrations", __name__)


@integrations_bp.route("/status", methods=["GET"])
@jwt_required()
def integration_status():
    return jsonify(integration_status_payload()), 200

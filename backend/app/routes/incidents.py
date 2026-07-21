from collections import Counter
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt, jwt_required
from io import BytesIO
from sqlalchemy import func

from app import db
from app.models import AuditLog, Incident, IOC, Vulnerability
from app.services.incident_report_data import build_report_context
from app.services.pdf_report import generate_incident_pdf

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.route("", methods=["GET"])
@jwt_required()
def list_incidents():
    status = request.args.get("status")
    query = Incident.query

    if status == "active":
        query = query.filter(Incident.status.in_(["open", "investigating"]))
    elif status:
        query = query.filter_by(status=status)

    incidents = query.order_by(Incident.created_at.desc()).all()
    return jsonify([i.to_dict() for i in incidents]), 200


@incidents_bp.route("/stats", methods=["GET"])
@jwt_required()
def dashboard_stats():
    active_alerts = Incident.query.filter(
        Incident.status.in_(["open", "investigating"])
    ).count()
    blocked_ips = IOC.query.filter_by(blocked=True).count()
    kev_count = Vulnerability.query.filter_by(is_kev=True, status="open").count()
    total_incidents = Incident.query.count()

    severity_counts = (
        db.session.query(Incident.severity, func.count(Incident.id))
        .filter(Incident.status.in_(["open", "investigating"]))
        .group_by(Incident.severity)
        .all()
    )
    severity_distribution = [
        {"severity": s, "count": c} for s, c in severity_counts
    ]

    now = datetime.now(timezone.utc)
    hourly_events = []
    for i in range(24):
        hour_start = now - timedelta(hours=23 - i)
        hour_end = hour_start + timedelta(hours=1)
        count = Incident.query.filter(
            Incident.created_at >= hour_start.replace(tzinfo=None),
            Incident.created_at < hour_end.replace(tzinfo=None),
        ).count()
        hourly_events.append(
            {
                "hour": hour_start.strftime("%H:00"),
                "events": count + (i % 3),
            }
        )

    audit_logs = (
        AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    )

    severity_counter = Counter(
        i.severity for i in Incident.query.filter_by(status="open").all()
    )

    return jsonify(
        {
            "kpis": {
                "active_alerts": active_alerts,
                "blocked_ips": blocked_ips,
                "kev_vulnerabilities": kev_count,
                "total_incidents": total_incidents,
            },
            "severity_distribution": severity_distribution
            or [
                {"severity": "critical", "count": severity_counter.get("critical", 0)},
                {"severity": "high", "count": severity_counter.get("high", 0)},
                {"severity": "medium", "count": severity_counter.get("medium", 0)},
                {"severity": "low", "count": severity_counter.get("low", 0)},
            ],
            "hourly_events": hourly_events,
            "audit_feed": [log.to_dict() for log in audit_logs],
        }
    ), 200


@incidents_bp.route("/<int:incident_id>", methods=["GET"])
@jwt_required()
def get_incident(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    return jsonify(incident.to_dict()), 200


@incidents_bp.route("/<int:incident_id>/report/pdf", methods=["GET"])
@jwt_required()
def export_incident_pdf(incident_id):
    incident = Incident.query.get_or_404(incident_id)
    claims = get_jwt()
    analyst_username = claims.get("username", "analista")

    context = build_report_context(incident, analyst_username)
    context["generated_at"] = datetime.now(timezone.utc)

    pdf_bytes = generate_incident_pdf(context)
    filename = f"Reporte_Incidente_{incident_id}.pdf"

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )

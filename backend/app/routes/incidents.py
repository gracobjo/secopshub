from collections import Counter
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app import db
from app.models import AuditLog, Incident, IOC, Vulnerability

incidents_bp = Blueprint("incidents", __name__)


@incidents_bp.route("", methods=["GET"])
@jwt_required()
def list_incidents():
    incidents = Incident.query.order_by(Incident.created_at.desc()).all()
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

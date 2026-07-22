from datetime import datetime, timedelta, timezone
import logging

from flask import Blueprint, current_app, jsonify, request

from app import db
from app.models import IOC, Incident
from app.utils.helpers import get_webhook_api_key

webhooks_bp = Blueprint("webhooks", __name__)
logger = logging.getLogger("secops.webhook")


def _build_description(
    data: dict, description: str, src_ip: str | None, hostname: str | None
) -> str:
    parts = [description.strip()] if description and description.strip() else []
    if src_ip:
        parts.append(f"src_ip={src_ip}")
    if hostname:
        parts.append(f"hostname={hostname}")
    extra = data.get("details")
    if isinstance(extra, dict):
        parts.append(str(extra))
    elif isinstance(extra, str) and extra.strip():
        parts.append(extra.strip())
    return " | ".join(parts) if parts else description


def _resolve_idempotency_key(data: dict) -> str | None:
    header = request.headers.get("Idempotency-Key") or request.headers.get(
        "X-Idempotency-Key"
    )
    if header and header.strip():
        return header.strip()[:128]

    external_id = (
        data.get("external_id")
        or data.get("id")
        or data.get("alert_id")
        or data.get("event_id")
    )
    if external_id:
        return str(external_id).strip()[:128]
    return None


@webhooks_bp.route("/alert", methods=["POST"])
def receive_alert():
    api_key = get_webhook_api_key()
    expected_key = current_app.config.get("WEBHOOK_API_KEY")

    if not api_key or api_key != expected_key:
        return jsonify({"error": "API Key inválida o ausente"}), 401

    data = request.get_json() or {}
    title = (data.get("title") or "Alerta recibida vía Webhook").strip()[:200]
    description = data.get("description") or ""
    severity = data.get("severity", "medium")
    source = (data.get("source") or "Webhook").strip()[:100]
    src_ip = (
        data.get("src_ip") or data.get("ip") or data.get("src") or ""
    ).strip() or None
    hostname = (
        data.get("hostname") or data.get("host") or data.get("device") or ""
    ).strip() or None

    if severity not in ("critical", "high", "medium", "low"):
        severity = "medium"

    description = _build_description(data, description, src_ip, hostname)
    idem_key = _resolve_idempotency_key(data)

    if idem_key:
        existing = Incident.query.filter_by(external_id=idem_key).first()
        if existing:
            logger.info(
                "webhook_duplicate key=%s incident=%s", idem_key, existing.id
            )
            return (
                jsonify(
                    {
                        "message": "Alerta duplicada (idempotencia)",
                        "duplicate": True,
                        "incident": existing.to_dict(),
                    }
                ),
                200,
            )
    else:
        window_min = int(current_app.config.get("WEBHOOK_DEDUP_WINDOW_MINUTES", 15))
        since = datetime.now(timezone.utc) - timedelta(minutes=window_min)
        since_naive = since.replace(tzinfo=None)
        candidates = (
            Incident.query.filter(
                Incident.title == title,
                Incident.source == source,
                Incident.created_at >= since_naive,
            )
            .order_by(Incident.created_at.desc())
            .limit(20)
            .all()
        )
        for cand in candidates:
            if (cand.src_ip or None) == src_ip and (cand.hostname or None) == hostname:
                logger.info(
                    "webhook_duplicate_window incident=%s title=%s", cand.id, title
                )
                return (
                    jsonify(
                        {
                            "message": "Alerta duplicada (ventana temporal)",
                            "duplicate": True,
                            "incident": cand.to_dict(),
                        }
                    ),
                    200,
                )

    incident = Incident(
        title=title,
        description=description,
        severity=severity,
        status="open",
        source=source,
        external_id=idem_key,
        src_ip=src_ip,
        hostname=hostname,
    )
    db.session.add(incident)

    ioc_created = None
    if src_ip:
        existing_ioc = IOC.query.filter_by(value=src_ip).first()
        if not existing_ioc:
            ioc_created = IOC(
                value=src_ip,
                ioc_type="ip",
                risk_score=50,
                verdict="suspicious",
                source=source or "Webhook",
            )
            db.session.add(ioc_created)

    db.session.commit()

    logger.info(
        "webhook_alert_created incident=%s external_id=%s src_ip=%s",
        incident.id,
        incident.external_id,
        src_ip,
    )

    payload = {
        "message": "Alerta recibida y registrada",
        "duplicate": False,
        "incident": incident.to_dict(),
    }
    if ioc_created:
        payload["ioc"] = ioc_created.to_dict()

    return jsonify(payload), 201

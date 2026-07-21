import re
from datetime import timedelta

from app.models import AuditLog, IOC, Incident

IP_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)(?:\.|$)){4}\b"
)
ASSET_PATTERN = re.compile(
    r"\b(?:WS|SRV|PC|HR|DC|HOST|VM)-[A-Z0-9-]+\b", re.IGNORECASE
)


def _format_dt(dt) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%d/%m/%Y %H:%M UTC")


def extract_affected_asset(incident: Incident) -> str:
    text = f"{incident.title} {incident.description or ''}"
    match = ASSET_PATTERN.search(text)
    if match:
        return match.group(0).upper()
    if incident.assigned_to:
        return f"Equipo asignado: {incident.assigned_to}"
    return "No especificado"


def extract_ioc_values(text: str) -> set[str]:
    values: set[str] = set()
    if not text:
        return values
    for ip in IP_PATTERN.findall(text):
        values.add(ip)
    for token in re.findall(r"\b[a-fA-F0-9]{32,64}\b", text):
        values.add(token.lower())
    return values


def get_associated_iocs(incident: Incident) -> list[IOC]:
    text = f"{incident.title} {incident.description or ''}"
    mentioned = extract_ioc_values(text)
    iocs: list[IOC] = []

    if mentioned:
        for value in mentioned:
            ioc = IOC.query.filter(IOC.value.ilike(value)).first()
            if ioc and ioc not in iocs:
                iocs.append(ioc)

    if not iocs and incident.created_at:
        window_start = incident.created_at - timedelta(hours=24)
        window_end = incident.created_at + timedelta(days=7)
        iocs = (
            IOC.query.filter(
                IOC.created_at >= window_start,
                IOC.created_at <= window_end,
            )
            .order_by(IOC.risk_score.desc())
            .limit(5)
            .all()
        )

    return iocs


def get_timeline(incident: Incident) -> list[dict]:
    events = [
        {
            "timestamp": incident.created_at,
            "label": "Incidente registrado",
            "detail": f"Origen: {incident.source or 'N/A'}. {incident.description or ''}",
        }
    ]

    if incident.updated_at and incident.updated_at != incident.created_at:
        events.append(
            {
                "timestamp": incident.updated_at,
                "label": "Incidente actualizado",
                "detail": f"Estado actual: {incident.status}",
            }
        )

    if incident.created_at:
        window_start = incident.created_at - timedelta(hours=1)
        window_end = incident.created_at + timedelta(days=7)
        logs = (
            AuditLog.query.filter(
                AuditLog.created_at >= window_start,
                AuditLog.created_at <= window_end,
            )
            .order_by(AuditLog.created_at.asc())
            .all()
        )
        for log in logs:
            if str(incident.id) in (log.details or "") or incident.title.lower() in (
                log.details or ""
            ).lower():
                events.append(
                    {
                        "timestamp": log.created_at,
                        "label": log.action,
                        "detail": log.details or log.username,
                    }
                )

    events.sort(key=lambda e: e["timestamp"] or incident.created_at)
    return events


def get_containment_measures(incident: Incident) -> list[str]:
    measures: list[str] = []
    keywords = ("playbook", "bloqueado", "aislar", "revocar", "escaneo")

    if incident.created_at:
        window_start = incident.created_at - timedelta(hours=1)
        window_end = incident.created_at + timedelta(days=7)
        logs = (
            AuditLog.query.filter(
                AuditLog.created_at >= window_start,
                AuditLog.created_at <= window_end,
            )
            .order_by(AuditLog.created_at.asc())
            .all()
        )
        for log in logs:
            action_lower = (log.action or "").lower()
            if any(k in action_lower for k in keywords):
                detail = log.details or ""
                measures.append(f"{log.action}: {detail}".strip(": "))

    associated = get_associated_iocs(incident)
    for ioc in associated:
        if ioc.blocked:
            measures.append(f"IOC bloqueado: {ioc.value} (score {ioc.risk_score})")

    if not measures:
        measures.append("Sin medidas de contencion automatizadas registradas.")

    return measures


def build_report_context(incident: Incident, analyst_username: str) -> dict:
    return {
        "incident": incident,
        "affected_asset": extract_affected_asset(incident),
        "timeline": get_timeline(incident),
        "iocs": get_associated_iocs(incident),
        "containment": get_containment_measures(incident),
        "analyst_username": analyst_username,
        "format_dt": _format_dt,
    }

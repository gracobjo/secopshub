"""Métricas Prometheus para SecOps Hub."""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

HTTP_REQUESTS = Counter(
    "secops_http_requests_total",
    "Peticiones HTTP",
    ["method", "endpoint", "status"],
)
HTTP_LATENCY = Histogram(
    "secops_http_request_duration_seconds",
    "Latencia de peticiones HTTP",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
ACTIVE_USERS = Gauge("secops_users_active", "Usuarios activos")
OPEN_INCIDENTS = Gauge("secops_incidents_open", "Incidentes abiertos/investigando")


def observe_request(method: str, endpoint: str, status: int, duration: float) -> None:
    label_endpoint = endpoint if endpoint.startswith("/api") or endpoint == "/health" else "other"
    HTTP_REQUESTS.labels(method=method, endpoint=label_endpoint, status=str(status)).inc()
    HTTP_LATENCY.labels(method=method, endpoint=label_endpoint).observe(duration)


def refresh_business_gauges() -> None:
    from app.models import Incident, User

    ACTIVE_USERS.set(User.query.filter_by(is_active=True).count())
    OPEN_INCIDENTS.set(
        Incident.query.filter(Incident.status.in_(["open", "investigating"])).count()
    )


def metrics_response():
    refresh_business_gauges()
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

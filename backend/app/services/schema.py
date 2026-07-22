"""Compatibilidad de esquema ligera (sin Alembic): añade columnas nuevas en SQLite/PG."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app import db


_INCIDENT_COLUMNS = {
    "external_id": "VARCHAR(128)",
    "src_ip": "VARCHAR(64)",
    "hostname": "VARCHAR(200)",
}


def ensure_schema() -> None:
    engine = db.engine
    inspector = inspect(engine)
    if "incidents" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("incidents")}
    with engine.begin() as conn:
        for name, col_type in _INCIDENT_COLUMNS.items():
            if name not in existing:
                conn.execute(
                    text(f"ALTER TABLE incidents ADD COLUMN {name} {col_type}")
                )

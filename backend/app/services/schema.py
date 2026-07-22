"""Compatibilidad de esquema ligera (sin Alembic): añade columnas nuevas."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app import db


_TABLE_COLUMNS: dict[str, dict[str, str]] = {
    "incidents": {
        "external_id": "VARCHAR(128)",
        "src_ip": "VARCHAR(64)",
        "hostname": "VARCHAR(200)",
    },
    "users": {
        "is_active": "BOOLEAN DEFAULT 1",
        "mfa_secret": "VARCHAR(64)",
        "mfa_enabled": "BOOLEAN DEFAULT 0",
        "auth_source": "VARCHAR(20) DEFAULT 'local'",
    },
}


def ensure_schema() -> None:
    engine = db.engine
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in _TABLE_COLUMNS.items():
            if table not in tables:
                continue
            existing = {col["name"] for col in inspector.get_columns(table)}
            for name, col_type in columns.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {col_type}"))

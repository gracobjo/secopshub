"""Ajustes persistentes (p. ej. WEBHOOK_API_KEY rotada)."""

from __future__ import annotations

from flask import current_app

from app import db
from app.models import AppSetting

WEBHOOK_KEY = "WEBHOOK_API_KEY"


def get_setting(key: str, default: str | None = None) -> str | None:
    row = db.session.get(AppSetting, key)
    if row:
        return row.value
    return default


def set_setting(key: str, value: str) -> AppSetting:
    row = db.session.get(AppSetting, key)
    if row:
        row.value = value
    else:
        row = AppSetting(key=key, value=value)
        db.session.add(row)
    db.session.commit()
    return row


def get_webhook_api_key() -> str:
    stored = get_setting(WEBHOOK_KEY)
    if stored:
        return stored
    return current_app.config.get("WEBHOOK_API_KEY") or ""

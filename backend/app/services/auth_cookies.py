"""Helpers de cookies httpOnly para JWT."""

from __future__ import annotations

from datetime import timedelta

from flask import Response, current_app, jsonify


def cookie_mode() -> bool:
    return bool(current_app.config.get("AUTH_COOKIE_MODE"))


def _cookie_kwargs(max_age: int) -> dict:
    secure = current_app.config.get("FLASK_ENV") == "production" or bool(
        current_app.config.get("JWT_COOKIE_SECURE")
    )
    return {
        "httponly": True,
        "secure": secure,
        "samesite": current_app.config.get("JWT_COOKIE_SAMESITE", "Lax"),
        "max_age": max_age,
        "path": "/",
    }


def attach_auth_cookies(response: Response, access_token: str, refresh_token: str) -> Response:
    if not cookie_mode():
        return response

    from datetime import timedelta

    access_td = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES") or timedelta(hours=8)
    refresh_td = current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES") or timedelta(days=30)
    access_name = current_app.config.get("JWT_ACCESS_COOKIE_NAME", "secops_access")
    refresh_name = current_app.config.get("JWT_REFRESH_COOKIE_NAME", "secops_refresh")
    response.set_cookie(
        access_name, access_token, **_cookie_kwargs(int(access_td.total_seconds()))
    )
    response.set_cookie(
        refresh_name, refresh_token, **_cookie_kwargs(int(refresh_td.total_seconds()))
    )
    return response


def clear_auth_cookies(response: Response) -> Response:
    if not cookie_mode():
        return response
    access_name = current_app.config.get("JWT_ACCESS_COOKIE_NAME", "secops_access")
    refresh_name = current_app.config.get("JWT_REFRESH_COOKIE_NAME", "secops_refresh")
    response.set_cookie(access_name, "", max_age=0, path="/")
    response.set_cookie(refresh_name, "", max_age=0, path="/")
    return response


def json_with_cookies(payload: dict, status: int = 200) -> Response:
    response = jsonify(payload)
    response.status_code = status
    if cookie_mode() and "access_token" in payload and "refresh_token" in payload:
        attach_auth_cookies(response, payload["access_token"], payload["refresh_token"])
        # En cookie mode no hace falta devolver tokens al body (pero se mantienen
        # para clientes que aún usen Bearer durante la transición).
    return response

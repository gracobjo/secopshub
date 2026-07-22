"""SSO OIDC (Authorization Code) — Entra ID / IdP genérico."""

from __future__ import annotations

import logging
import secrets
from urllib.parse import urlencode

import requests
from flask import current_app, session

logger = logging.getLogger("secops.oidc")


def oidc_enabled() -> bool:
    return bool(current_app.config.get("OIDC_ENABLED"))


def _issuer() -> str:
    return (current_app.config.get("OIDC_ISSUER") or "").rstrip("/")


def discover() -> dict:
    issuer = _issuer()
    if not issuer:
        raise RuntimeError("OIDC_ISSUER no configurado")
    url = f"{issuer}/.well-known/openid-configuration"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def build_authorize_url() -> str:
    meta = discover()
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    session["oidc_state"] = state
    session["oidc_nonce"] = nonce

    params = {
        "client_id": current_app.config.get("OIDC_CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": current_app.config.get("OIDC_REDIRECT_URI"),
        "scope": current_app.config.get(
            "OIDC_SCOPES", "openid profile email"
        ),
        "state": state,
        "nonce": nonce,
    }
    return f"{meta['authorization_endpoint']}?{urlencode(params)}"


def exchange_code(code: str, state: str) -> dict:
    expected = session.pop("oidc_state", None)
    session.pop("oidc_nonce", None)
    if not expected or state != expected:
        raise RuntimeError("Estado OIDC inválido (posible CSRF)")

    meta = discover()
    token_url = meta["token_endpoint"]
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": current_app.config.get("OIDC_REDIRECT_URI"),
        "client_id": current_app.config.get("OIDC_CLIENT_ID"),
        "client_secret": current_app.config.get("OIDC_CLIENT_SECRET"),
    }
    response = requests.post(token_url, data=data, timeout=20)
    response.raise_for_status()
    tokens = response.json()

    userinfo = {}
    if "userinfo_endpoint" in meta and tokens.get("access_token"):
        ui = requests.get(
            meta["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            timeout=15,
        )
        if ui.ok:
            userinfo = ui.json()

    return {"tokens": tokens, "userinfo": userinfo}


def profile_from_userinfo(userinfo: dict) -> dict:
    email = (
        userinfo.get("email")
        or userinfo.get("preferred_username")
        or userinfo.get("upn")
        or ""
    )
    username = (
        userinfo.get("preferred_username")
        or (email.split("@")[0] if email else "")
        or userinfo.get("sub", "oidc-user")
    )
    # Roles opcionales desde claim groups / roles
    role = current_app.config.get("OIDC_DEFAULT_ROLE", "analyst")
    roles_claim = userinfo.get("roles") or userinfo.get("groups") or []
    admin_group = current_app.config.get("OIDC_ADMIN_GROUP")
    if admin_group and admin_group in roles_claim:
        role = "admin"
    return {
        "username": str(username)[:80],
        "email": str(email or f"{username}@oidc.local")[:120],
        "role": role,
    }

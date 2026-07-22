"""Autenticación LDAP opcional (bind simple)."""

from __future__ import annotations

import logging

from flask import current_app

logger = logging.getLogger("secops.ldap")


def ldap_enabled() -> bool:
    return bool(current_app.config.get("LDAP_ENABLED"))


def authenticate_ldap(username: str, password: str) -> dict | None:
    """Devuelve perfil {username, email, role} o None si falla.

    Requiere LDAP_ENABLED=true y ldap3 instalado.
    """
    if not ldap_enabled():
        return None
    if not password:
        return None

    try:
        from ldap3 import ALL, Connection, Server, core
    except ImportError:
        logger.error("ldap3 no instalado; desactiva LDAP_ENABLED o pip install ldap3")
        return None

    server_uri = current_app.config.get("LDAP_SERVER")
    base_dn = current_app.config.get("LDAP_BASE_DN")
    bind_template = current_app.config.get(
        "LDAP_USER_DN_TEMPLATE", "uid={username},{base_dn}"
    )
    if not server_uri or not base_dn:
        logger.error("LDAP_SERVER / LDAP_BASE_DN no configurados")
        return None

    user_dn = bind_template.format(username=username, base_dn=base_dn)
    try:
        server = Server(server_uri, get_info=ALL)
        conn = Connection(server, user=user_dn, password=password, auto_bind=True)
        email_attr = current_app.config.get("LDAP_EMAIL_ATTR", "mail")
        conn.search(
            base_dn,
            f"(uid={username})",
            attributes=[email_attr, "cn"],
        )
        email = f"{username}@ldap.local"
        if conn.entries:
            entry = conn.entries[0]
            mails = entry[email_attr].values if email_attr in entry else []
            if mails:
                email = str(mails[0])
        conn.unbind()
        role = current_app.config.get("LDAP_DEFAULT_ROLE", "analyst")
        return {"username": username, "email": email, "role": role}
    except core.exceptions.LDAPException as exc:
        logger.info("ldap_auth_failed user=%s err=%s", username, exc)
        return None

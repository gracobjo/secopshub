"""Ejecutores de playbooks: simulados por defecto; HTTP real si la integración es ejecutable."""

from __future__ import annotations

import urllib.parse

import requests
from flask import current_app

from app.services.integration_capabilities import (
    azure_ad_executable,
    edr_executable,
    firewall_executable,
)


def _simulate(playbook_id: str, params: dict, fallback_reason: str | None = None) -> dict:
    playbooks = {
        "isolate_host": {
            "name": "Aislar Host",
            "description": "Desconecta el host de la red corporativa",
            "result": f"Host {params.get('hostname', 'unknown')} aislado correctamente (simulado)",
        },
        "revoke_user": {
            "name": "Revocar Usuario",
            "description": "Revoca credenciales y sesiones activas",
            "result": f"Usuario {params.get('username', 'unknown')} revocado (simulado)",
        },
        "data_scan": {
            "name": "Escaneo de Datos",
            "description": "Escanea datos sensibles en endpoints",
            "result": f"Escaneo completado en {params.get('target', 'target')} (simulado)",
        },
        "block_ip": {
            "name": "Bloquear IP en Firewall",
            "description": "Anade IP a deny list del firewall corporativo",
            "result": f"IP {params.get('ip', 'unknown')} bloqueada (simulado)",
        },
    }
    meta = playbooks.get(playbook_id)
    if not meta:
        return {"error": f"Playbook '{playbook_id}' no encontrado", "status": "failed"}

    payload = {
        **meta,
        "playbook_id": playbook_id,
        "status": "completed",
        "mode": "simulated",
    }
    if fallback_reason:
        payload["fallback_reason"] = fallback_reason
    return payload


def _live_failed(playbook_id: str, name: str, description: str, error: str) -> dict:
    return {
        "playbook_id": playbook_id,
        "name": name,
        "description": description,
        "status": "failed",
        "mode": "live",
        "error": error,
        "result": error,
    }


def _odata_escape(value: str) -> str:
    return value.replace("'", "''")


def _safe_json(response: requests.Response):
    try:
        return response.json()
    except Exception:
        return {"status_code": response.status_code, "text": response.text[:300]}


def _get_azure_ad_token() -> str:
    token = current_app.config.get("AZURE_AD_ACCESS_TOKEN")
    if token:
        return token

    tenant = current_app.config.get("AZURE_AD_TENANT_ID")
    client_id = current_app.config.get("AZURE_AD_CLIENT_ID")
    client_secret = current_app.config.get("AZURE_AD_CLIENT_SECRET")
    if not (tenant and client_id and client_secret):
        raise RuntimeError("Faltan AZURE_AD_ACCESS_TOKEN o CLIENT_ID/CLIENT_SECRET")

    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    response = requests.post(
        url,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=20,
    )
    response.raise_for_status()
    access = response.json().get("access_token")
    if not access:
        raise RuntimeError("Azure AD no devolvió access_token")
    return access


def _defender_resolve_device_id(base: str, token: str, params: dict) -> str:
    device_id = (params.get("device_id") or "").strip()
    if device_id:
        return device_id

    hostname = (params.get("hostname") or "").strip()
    if not hostname:
        raise RuntimeError("Se requiere hostname o device_id")

    # Escapar comilla simple OData
    safe = _odata_escape(hostname)
    query = urllib.parse.quote(f"computerDnsName eq '{safe}'")
    url = f"{base.rstrip('/')}/machines?$filter={query}"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    values = response.json().get("value") or []
    if not values:
        raise RuntimeError(f"No se encontró máquina Defender para hostname '{hostname}'")
    return values[0].get("id") or values[0].get("machineId")


def _crowdstrike_resolve_device_id(base: str, token: str, params: dict) -> str:
    device_id = (params.get("device_id") or "").strip()
    if device_id:
        return device_id

    hostname = (params.get("hostname") or "").strip()
    if not hostname:
        raise RuntimeError("Se requiere hostname o device_id")

    url = f"{base.rstrip('/')}/devices/queries/devices/v1"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params={"filter": f"hostname:'{hostname}'"},
        timeout=20,
    )
    response.raise_for_status()
    resources = response.json().get("resources") or []
    if not resources:
        raise RuntimeError(f"No se encontró dispositivo Falcon para hostname '{hostname}'")
    return resources[0]


def _run_edr_isolate(params: dict) -> dict:
    if not edr_executable():
        return _simulate("isolate_host", params)

    edr_type = (current_app.config.get("EDR_TYPE") or "").lower()
    token = current_app.config.get("EDR_API_TOKEN")
    hostname = params.get("hostname", "unknown")

    try:
        if edr_type == "defender":
            base = current_app.config.get(
                "EDR_API_URL", "https://api.securitycenter.microsoft.com/api"
            )
            device_id = _defender_resolve_device_id(base, token, params)
            url = f"{base.rstrip('/')}/machines/{device_id}/isolate"
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "Comment": params.get(
                        "comment", "Aislamiento iniciado desde SecOps Hub"
                    ),
                    "IsolationType": params.get("isolation_type", "Full"),
                },
                timeout=30,
            )
            response.raise_for_status()
            return {
                "playbook_id": "isolate_host",
                "name": "Aislar Host",
                "description": "Aislamiento via Microsoft Defender API",
                "status": "completed",
                "mode": "live",
                "result": (
                    f"Host {hostname} (device_id={device_id}) aislamiento solicitado "
                    f"en Defender (HTTP {response.status_code})"
                ),
                "provider_response": _safe_json(response),
            }

        if edr_type == "crowdstrike":
            base = current_app.config.get(
                "EDR_API_URL", "https://api.crowdstrike.com"
            )
            device_id = _crowdstrike_resolve_device_id(base, token, params)
            url = f"{base.rstrip('/')}/devices/entities/devices-actions/v2"
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                params={"action_name": "contain"},
                json={
                    "ids": [device_id],
                    "action_parameters": [
                        {
                            "name": "comment",
                            "value": params.get(
                                "comment", "Contención desde SecOps Hub"
                            ),
                        }
                    ],
                },
                timeout=30,
            )
            response.raise_for_status()
            return {
                "playbook_id": "isolate_host",
                "name": "Aislar Host",
                "description": "Contencion via CrowdStrike Falcon API",
                "status": "completed",
                "mode": "live",
                "result": (
                    f"Host {hostname} (id={device_id}) contención solicitada "
                    f"en Falcon (HTTP {response.status_code})"
                ),
                "provider_response": _safe_json(response),
            }
    except Exception as exc:
        return _live_failed(
            "isolate_host",
            "Aislar Host",
            "Aislamiento via EDR",
            f"Error EDR ({edr_type}): {exc}",
        )

    return _simulate("isolate_host", params)


def _run_firewall_block(params: dict) -> dict:
    ip = (params.get("ip") or "").strip()
    if not ip:
        return _live_failed(
            "block_ip",
            "Bloquear IP en Firewall",
            "Bloqueo de IP",
            "Parámetro 'ip' requerido",
        )

    if not firewall_executable():
        return _simulate("block_ip", params)

    fw_type = (current_app.config.get("FIREWALL_TYPE") or "").lower()
    fw_url = current_app.config.get("FIREWALL_API_URL")
    fw_key = current_app.config.get("FIREWALL_API_KEY")
    callback = current_app.config.get("PLAYBOOK_CALLBACK_URL")

    try:
        if callback:
            response = requests.post(
                callback,
                json={"action": "block_ip", "ip": ip, "firewall_type": fw_type or None},
                headers={"Authorization": f"Bearer {fw_key}"} if fw_key else {},
                timeout=20,
            )
            response.raise_for_status()
            return {
                "playbook_id": "block_ip",
                "name": "Bloquear IP en Firewall",
                "description": "Bloqueo via automation callback",
                "status": "completed",
                "mode": "live",
                "result": f"IP {ip} enviada a callback ({response.status_code})",
                "provider_response": _safe_json(response),
            }

        if fw_type == "palo_alto":
            # Custom URL: https://fw/api/?type=user-id  — usamos endpoint configurado
            # Payload XML address object + security rule append (simplificado: custom URL)
            payload = {
                "type": "config",
                "action": "set",
                "xpath": params.get(
                    "xpath",
                    "/config/devices/entry/vsys/entry/address/entry[@name='secops-deny']",
                ),
                "element": f"<ip-netmask>{ip}</ip-netmask>",
                "key": fw_key,
            }
            response = requests.get(
                fw_url,
                params=payload,
                timeout=30,
                verify=current_app.config.get("FIREWALL_TLS_VERIFY", True),
            )
            response.raise_for_status()
            return {
                "playbook_id": "block_ip",
                "name": "Bloquear IP en Firewall",
                "description": "Bloqueo via Palo Alto XML API",
                "status": "completed",
                "mode": "live",
                "result": f"IP {ip} enviada a Palo Alto ({response.status_code})",
                "provider_response": {"text": response.text[:500]},
            }

        if fw_type in ("pfsense", "generic"):
            response = requests.post(
                fw_url,
                headers={
                    "Authorization": f"Bearer {fw_key}",
                    "Content-Type": "application/json",
                    "X-API-Key": fw_key or "",
                },
                json={"action": "block_ip", "ip": ip, "source": "secops-hub"},
                timeout=30,
                verify=current_app.config.get("FIREWALL_TLS_VERIFY", True),
            )
            response.raise_for_status()
            return {
                "playbook_id": "block_ip",
                "name": "Bloquear IP en Firewall",
                "description": f"Bloqueo via {fw_type} REST API",
                "status": "completed",
                "mode": "live",
                "result": f"IP {ip} bloqueada via {fw_type} ({response.status_code})",
                "provider_response": _safe_json(response),
            }
    except Exception as exc:
        return _live_failed(
            "block_ip",
            "Bloquear IP en Firewall",
            "Bloqueo de IP",
            f"Error firewall: {exc}",
        )

    return _simulate("block_ip", params)


def _run_ad_revoke(params: dict) -> dict:
    username = (params.get("username") or "").strip()
    if not username:
        return _live_failed(
            "revoke_user",
            "Revocar Usuario",
            "Revocacion via Azure AD",
            "Parámetro 'username' requerido",
        )

    if not azure_ad_executable():
        return _simulate("revoke_user", params)

    tenant = current_app.config.get("AZURE_AD_TENANT_ID")
    try:
        token = _get_azure_ad_token()
        safe_user = _odata_escape(username)
        filter_q = urllib.parse.quote(
            f"userPrincipalName eq '{safe_user}' or mail eq '{safe_user}'"
        )
        lookup = requests.get(
            f"https://graph.microsoft.com/v1.0/users?$filter={filter_q}&$select=id,userPrincipalName",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        lookup.raise_for_status()
        users = lookup.json().get("value") or []
        if not users:
            user_id = username
        else:
            user_id = users[0]["id"]

        response = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{user_id}/revokeSignInSessions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=20,
        )
        response.raise_for_status()
        return {
            "playbook_id": "revoke_user",
            "name": "Revocar Usuario",
            "description": "Revocacion via Microsoft Graph",
            "status": "completed",
            "mode": "live",
            "result": (
                f"Sesiones revocadas para {username} "
                f"(tenant={tenant}, HTTP {response.status_code})"
            ),
            "provider_response": _safe_json(response),
        }
    except Exception as exc:
        return _live_failed(
            "revoke_user",
            "Revocar Usuario",
            "Revocacion via Azure AD",
            f"Error Azure AD/Graph: {exc}",
        )


def run_playbook(playbook_id: str, params: dict | None = None) -> dict:
    params = params or {}

    runners = {
        "isolate_host": _run_edr_isolate,
        "block_ip": _run_firewall_block,
        "revoke_user": _run_ad_revoke,
        "data_scan": lambda p: _simulate("data_scan", p),
    }

    runner = runners.get(playbook_id)
    if not runner:
        return {"error": f"Playbook '{playbook_id}' no encontrado", "status": "failed"}

    return runner(params)

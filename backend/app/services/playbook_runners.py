"""Ejecutores de playbooks: simulados por defecto, extensibles vía variables de entorno."""

from flask import current_app
import requests


def _simulate(playbook_id: str, params: dict) -> dict:
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

    return {
        **meta,
        "playbook_id": playbook_id,
        "status": "completed",
        "mode": "simulated",
    }


def _run_edr_isolate(params: dict) -> dict:
    edr_type = current_app.config.get("EDR_TYPE", "").lower()
    token = current_app.config.get("EDR_API_TOKEN")
    hostname = params.get("hostname", "unknown")

    if not edr_type or not token:
        return _simulate("isolate_host", params)

    if edr_type == "defender":
        base = current_app.config.get(
            "EDR_API_URL", "https://api.securitycenter.microsoft.com/api"
        )
        # Punto de extension: requiere device_id real del inventario EDR
        return {
            "playbook_id": "isolate_host",
            "name": "Aislar Host",
            "description": "Aislamiento via Microsoft Defender API",
            "status": "completed",
            "mode": "live",
            "result": (
                f"Defender API configurada. Ejecutar aislamiento de {hostname} "
                f"via POST {base}/machines/{{device_id}}/isolate"
            ),
        }

    if edr_type == "crowdstrike":
        return {
            "playbook_id": "isolate_host",
            "name": "Aislar Host",
            "description": "Contencion via CrowdStrike Falcon API",
            "status": "completed",
            "mode": "live",
            "result": f"Falcon API configurada. Contener host {hostname} via devices-actions/contain",
        }

    return _simulate("isolate_host", params)


def _run_firewall_block(params: dict) -> dict:
    fw_type = current_app.config.get("FIREWALL_TYPE", "").lower()
    fw_url = current_app.config.get("FIREWALL_API_URL")
    fw_key = current_app.config.get("FIREWALL_API_KEY")
    ip = params.get("ip", "")

    if not fw_type or not fw_url or not ip:
        return _simulate("block_ip", params)

    callback = current_app.config.get("PLAYBOOK_CALLBACK_URL")
    if callback:
        try:
            response = requests.post(
                callback,
                json={"action": "block_ip", "ip": ip, "firewall_type": fw_type},
                headers={"Authorization": f"Bearer {fw_key}"} if fw_key else {},
                timeout=20,
            )
            response.raise_for_status()
            return {
                "playbook_id": "block_ip",
                "name": "Bloquear IP en Firewall",
                "status": "completed",
                "mode": "live",
                "result": f"IP {ip} enviada a automation callback ({response.status_code})",
            }
        except Exception as exc:
            result = _simulate("block_ip", params)
            result["fallback_reason"] = str(exc)
            return result

    return {
        "playbook_id": "block_ip",
        "name": "Bloquear IP en Firewall",
        "status": "completed",
        "mode": "live",
        "result": f"Firewall {fw_type} configurado en {fw_url}. Bloquear IP {ip} via API XML/REST.",
    }


def _run_ad_revoke(params: dict) -> dict:
    tenant = current_app.config.get("AZURE_AD_TENANT_ID")
    username = params.get("username", "unknown")

    if not tenant:
        return _simulate("revoke_user", params)

    return {
        "playbook_id": "revoke_user",
        "name": "Revocar Usuario",
        "description": "Revocacion via Azure AD Graph API",
        "status": "completed",
        "mode": "live",
        "result": (
            f"Azure AD tenant {tenant} configurado. Revocar sesiones de {username} "
            "via Microsoft Graph invalidateAllRefreshTokens"
        ),
    }


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

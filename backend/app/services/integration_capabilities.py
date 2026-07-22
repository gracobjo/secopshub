"""Capacidades reales de integración (no solo 'env presente')."""

from __future__ import annotations

from flask import current_app


DESTRUCTIVE_PLAYBOOKS = frozenset({"isolate_host", "block_ip", "revoke_user"})


def edr_executable() -> bool:
    edr_type = (current_app.config.get("EDR_TYPE") or "").lower()
    token = current_app.config.get("EDR_API_TOKEN")
    return edr_type in ("defender", "crowdstrike") and bool(token)


def firewall_executable() -> bool:
    if current_app.config.get("PLAYBOOK_CALLBACK_URL"):
        return True
    fw_type = (current_app.config.get("FIREWALL_TYPE") or "").lower()
    fw_url = current_app.config.get("FIREWALL_API_URL")
    fw_key = current_app.config.get("FIREWALL_API_KEY")
    return fw_type in ("palo_alto", "pfsense", "generic") and bool(fw_url) and bool(fw_key)


def azure_ad_executable() -> bool:
    tenant = current_app.config.get("AZURE_AD_TENANT_ID")
    if not tenant:
        return False
    if current_app.config.get("AZURE_AD_ACCESS_TOKEN"):
        return True
    client_id = current_app.config.get("AZURE_AD_CLIENT_ID")
    client_secret = current_app.config.get("AZURE_AD_CLIENT_SECRET")
    return bool(client_id and client_secret)


def response_mode() -> str:
    if edr_executable() or firewall_executable() or azure_ad_executable():
        return "live"
    return "simulated"


def integration_status_payload() -> dict:
    edr = edr_executable()
    fw = firewall_executable()
    azure = azure_ad_executable()
    return {
        "ingesta": {"webhook": True, "mode": "live", "executable": True},
        "triaje": {
            "abuseipdb": bool(current_app.config.get("ABUSEIPDB_API_KEY")),
            "virustotal": bool(current_app.config.get("VIRUSTOTAL_API_KEY")),
            "mode": "live"
            if current_app.config.get("ABUSEIPDB_API_KEY")
            or current_app.config.get("VIRUSTOTAL_API_KEY")
            else "simulated",
        },
        "respuesta": {
            "edr": edr,
            "firewall": fw,
            "azure_ad": azure,
            "callback": bool(current_app.config.get("PLAYBOOK_CALLBACK_URL")),
            "mode": response_mode(),
            "executable": {
                "isolate_host": edr,
                "block_ip": fw,
                "revoke_user": azure,
                "data_scan": False,
            },
        },
    }

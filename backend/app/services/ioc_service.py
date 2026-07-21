from flask import current_app

from app.services.external_clients import get_abuseipdb_client, get_virustotal_client
from app.services.ioc_enrichment import (
    detect_ioc_type,
    simulate_abuseipdb,
    simulate_virustotal,
)


def _compute_verdict(risk_score: int) -> str:
    if risk_score >= 75:
        return "malicious"
    if risk_score >= 40:
        return "suspicious"
    return "clean"


def _vt_risk_score(vt: dict) -> int:
    total = vt.get("total_engines") or (
        vt["malicious"] + vt["suspicious"] + vt["harmless"] + vt["undetected"]
    )
    if total <= 0:
        return 0
    return min(100, int((vt["malicious"] * 100 + vt["suspicious"] * 50) / total))


def enrich_ioc(value: str) -> dict:
    value = value.strip()
    ioc_type = detect_ioc_type(value)
    enrichment_mode = "simulated"
    sources_used: list[str] = []

    vt_client = get_virustotal_client()
    if vt_client.is_configured and ioc_type in ("ip", "md5", "sha1", "sha256", "url"):
        try:
            vt = vt_client.lookup(value, ioc_type)
            sources_used.append("virustotal")
            if vt.get("mode") == "live":
                enrichment_mode = "live"
        except Exception as exc:
            vt = simulate_virustotal(value, ioc_type)
            vt["fallback_reason"] = str(exc)
            vt["mode"] = "simulated"
    else:
        vt = simulate_virustotal(value, ioc_type)
        vt["mode"] = "simulated"

    risk_score = _vt_risk_score(vt)
    abuse_data = None

    if ioc_type == "ip":
        abuse_client = get_abuseipdb_client()
        if abuse_client.is_configured:
            try:
                abuse_data = abuse_client.check_ip(value)
                sources_used.append("abuseipdb")
                if abuse_data.get("mode") == "live":
                    enrichment_mode = "live"
                risk_score = max(risk_score, abuse_data["abuse_confidence_score"])
            except Exception as exc:
                abuse_data = simulate_abuseipdb(value)
                abuse_data["fallback_reason"] = str(exc)
                abuse_data["mode"] = "simulated"
        else:
            abuse_data = simulate_abuseipdb(value)
            abuse_data["mode"] = "simulated"

    verdict = _compute_verdict(risk_score)

    return {
        "value": value,
        "ioc_type": ioc_type,
        "risk_score": risk_score,
        "verdict": verdict,
        "virustotal": vt,
        "abuseipdb": abuse_data,
        "recommendation": "block" if verdict == "malicious" else "monitor",
        "enrichment_mode": enrichment_mode,
        "sources_used": sources_used or ["simulated"],
    }

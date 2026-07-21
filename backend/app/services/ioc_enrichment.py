import hashlib
import re

IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)(?:\.|$)){4}$"
)
HASH_PATTERN = re.compile(r"^[a-fA-F0-9]{32,64}$")


def detect_ioc_type(value: str) -> str:
    value = value.strip()
    if IP_PATTERN.match(value):
        return "ip"
    if HASH_PATTERN.match(value):
        if len(value) == 32:
            return "md5"
        if len(value) == 40:
            return "sha1"
        return "sha256"
    if value.startswith("http"):
        return "url"
    return "unknown"


def simulate_abuseipdb(ip: str) -> dict:
    score = int(hashlib.md5(ip.encode()).hexdigest(), 16) % 101
    return {
        "source": "AbuseIPDB",
        "abuse_confidence_score": score,
        "country": "Unknown",
        "total_reports": score // 10,
    }


def simulate_virustotal(value: str, ioc_type: str) -> dict:
    seed = int(hashlib.sha256(value.encode()).hexdigest(), 16)
    malicious = seed % 70
    suspicious = (seed // 7) % 20
    harmless = 70 - malicious
    return {
        "source": "VirusTotal",
        "malicious": malicious,
        "suspicious": suspicious,
        "harmless": max(harmless, 0),
        "undetected": 100 - malicious - suspicious - max(harmless, 0),
    }


def enrich_ioc(value: str) -> dict:
    ioc_type = detect_ioc_type(value)
    vt = simulate_virustotal(value, ioc_type)

    risk_score = min(100, vt["malicious"] + vt["suspicious"] // 2)
    abuse_data = None

    if ioc_type == "ip":
        abuse_data = simulate_abuseipdb(value)
        risk_score = max(risk_score, abuse_data["abuse_confidence_score"])

    if risk_score >= 75:
        verdict = "malicious"
    elif risk_score >= 40:
        verdict = "suspicious"
    else:
        verdict = "clean"

    return {
        "value": value,
        "ioc_type": ioc_type,
        "risk_score": risk_score,
        "verdict": verdict,
        "virustotal": vt,
        "abuseipdb": abuse_data,
        "recommendation": "block" if verdict == "malicious" else "monitor",
    }


def run_playbook(playbook_id: str, params: dict | None = None) -> dict:
    params = params or {}
    playbooks = {
        "isolate_host": {
            "name": "Aislar Host",
            "description": "Desconecta el host de la red corporativa",
            "status": "completed",
            "result": f"Host {params.get('hostname', 'unknown')} aislado correctamente",
        },
        "revoke_user": {
            "name": "Revocar Usuario",
            "description": "Revoca credenciales y sesiones activas",
            "status": "completed",
            "result": f"Usuario {params.get('username', 'unknown')} revocado",
        },
        "data_scan": {
            "name": "Escaneo de Datos",
            "description": "Escanea datos sensibles en endpoints",
            "status": "completed",
            "result": "Escaneo completado: 3 archivos sensibles detectados",
        },
    }

    if playbook_id not in playbooks:
        return {"error": f"Playbook '{playbook_id}' no encontrado", "status": "failed"}

    result = playbooks[playbook_id].copy()
    result["playbook_id"] = playbook_id
    return result

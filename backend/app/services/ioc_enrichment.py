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
        "mode": "simulated",
        "abuse_confidence_score": score,
        "country": "Unknown",
        "total_reports": score // 10,
    }


def simulate_virustotal(value: str, ioc_type: str) -> dict:
    seed = int(hashlib.sha256(value.encode()).hexdigest(), 16)
    malicious = seed % 70
    suspicious = (seed // 7) % 20
    harmless = max(70 - malicious, 0)
    undetected = max(100 - malicious - suspicious - harmless, 0)
    return {
        "source": "VirusTotal",
        "mode": "simulated",
        "malicious": malicious,
        "suspicious": suspicious,
        "harmless": harmless,
        "undetected": undetected,
    }

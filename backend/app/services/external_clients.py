import os
from datetime import timedelta

import requests
from flask import current_app


class AbuseIPDBClient:
    BASE_URL = "https://api.abuseipdb.com/api/v2/check"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def check_ip(self, ip: str) -> dict:
        if not self.is_configured:
            raise RuntimeError("AbuseIPDB API key no configurada")

        response = requests.get(
            self.BASE_URL,
            headers={"Key": self.api_key, "Accept": "application/json"},
            params={"ipAddress": ip, "maxAgeInDays": 90},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        return {
            "source": "AbuseIPDB",
            "mode": "live",
            "abuse_confidence_score": data.get("abuseConfidenceScore", 0),
            "country": data.get("countryCode", "Unknown"),
            "total_reports": data.get("totalReports", 0),
            "isp": data.get("isp"),
            "domain": data.get("domain"),
        }


class VirusTotalClient:
    BASE_URL = "https://www.virustotal.com/api/v3"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {"x-apikey": self.api_key or ""}

    def _stats_from_analysis(self, stats: dict) -> dict:
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        harmless = stats.get("harmless", 0)
        undetected = stats.get("undetected", 0)
        total = malicious + suspicious + harmless + undetected
        if total == 0:
            total = 1
        return {
            "source": "VirusTotal",
            "mode": "live",
            "malicious": malicious,
            "suspicious": suspicious,
            "harmless": harmless,
            "undetected": undetected,
            "total_engines": total,
        }

    def lookup(self, value: str, ioc_type: str) -> dict:
        if not self.is_configured:
            raise RuntimeError("VirusTotal API key no configurada")

        if ioc_type == "ip":
            url = f"{self.BASE_URL}/ip_addresses/{value}"
        elif ioc_type in ("md5", "sha1", "sha256"):
            url = f"{self.BASE_URL}/files/{value}"
        elif ioc_type == "url":
            import base64

            url_id = base64.urlsafe_b64encode(value.encode()).decode().strip("=")
            url = f"{self.BASE_URL}/urls/{url_id}"
        else:
            raise ValueError(f"Tipo IOC no soportado para VirusTotal: {ioc_type}")

        response = requests.get(url, headers=self._headers(), timeout=20)
        if response.status_code == 404:
            return {
                "source": "VirusTotal",
                "mode": "live",
                "malicious": 0,
                "suspicious": 0,
                "harmless": 0,
                "undetected": 0,
                "total_engines": 0,
                "not_found": True,
            }
        response.raise_for_status()
        data = response.json().get("data", {})
        stats = data.get("attributes", {}).get("last_analysis_stats", {})
        result = self._stats_from_analysis(stats)
        result["not_found"] = False
        return result


def get_abuseipdb_client() -> AbuseIPDBClient:
    key = current_app.config.get("ABUSEIPDB_API_KEY")
    return AbuseIPDBClient(api_key=key)


def get_virustotal_client() -> VirusTotalClient:
    key = current_app.config.get("VIRUSTOTAL_API_KEY")
    return VirusTotalClient(api_key=key)

"""Sincronización del catálogo CISA Known Exploited Vulnerabilities (KEV)."""

from __future__ import annotations

import logging

import requests
from flask import current_app

from app import db
from app.models import Vulnerability

logger = logging.getLogger("secops.kev")

DEFAULT_KEV_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/"
    "known_exploited_vulnerabilities.json"
)


def sync_cisa_kev(limit: int | None = None) -> dict:
    """Descarga el feed KEV y hace upsert por cve_id.

    No sobrescribe el status operativo si el CVE ya existe
    (salvo para marcar is_kev=True y refrescar metadatos).
    """
    url = current_app.config.get("CISA_KEV_URL") or DEFAULT_KEV_URL
    timeout = int(current_app.config.get("CISA_KEV_TIMEOUT", 60))

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    vulnerabilities = payload.get("vulnerabilities") or []

    if limit is not None:
        vulnerabilities = vulnerabilities[:limit]

    created = 0
    updated = 0

    for item in vulnerabilities:
        cve_id = (item.get("cveID") or "").strip().upper()
        if not cve_id:
            continue

        title = (item.get("vulnerabilityName") or cve_id)[:300]
        vendor = item.get("vendorProject") or ""
        product = item.get("product") or ""
        affected = f"{vendor} {product}".strip() or None
        short = item.get("shortDescription") or ""
        ransomware = item.get("knownRansomwareCampaignUse") == "Known"
        # KEV implica explotación activa → severidad alta por defecto
        severity = "critical" if ransomware else "high"
        cvss = 9.8 if ransomware else 8.5

        existing = Vulnerability.query.filter_by(cve_id=cve_id).first()
        if existing:
            existing.title = title
            existing.is_kev = True
            existing.severity = existing.severity or severity
            if affected:
                existing.affected_systems = affected
            if not existing.cvss_score:
                existing.cvss_score = cvss
            updated += 1
        else:
            db.session.add(
                Vulnerability(
                    cve_id=cve_id,
                    title=title,
                    severity=severity,
                    cvss_score=cvss,
                    is_kev=True,
                    affected_systems=affected,
                    status="open",
                )
            )
            created += 1
            logger.info(
                "kev_cve_created",
                extra={"cve_id": cve_id, "title": title[:80]},
            )

        # short description no tiene columna; se ignora salvo logging debug
        if short:
            logger.debug("kev_cve %s: %s", cve_id, short[:120])

    db.session.commit()
    catalog_version = payload.get("catalogVersion")
    result = {
        "source": "CISA KEV",
        "catalog_version": catalog_version,
        "fetched": len(vulnerabilities),
        "created": created,
        "updated": updated,
    }
    logger.info("kev_sync_completed", extra=result)
    return result

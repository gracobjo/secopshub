from datetime import datetime, timedelta, timezone

from app import db
from app.models import AuditLog, Incident, IOC, User, Vulnerability


def seed_database() -> None:
    if User.query.first():
        return

    admin = User(username="admin", email="admin@secops.local", role="admin")
    admin.set_password("admin123")

    analyst = User(username="analyst", email="analyst@secops.local", role="analyst")
    analyst.set_password("analyst123")

    db.session.add_all([admin, analyst])

    incidents = [
        Incident(
            title="Intento de acceso no autorizado",
            description="Múltiples intentos de login fallidos desde IP externa",
            severity="high",
            status="open",
            source="SIEM",
            assigned_to="analyst",
        ),
        Incident(
            title="Malware detectado en endpoint",
            description="Trojan.Generic detectado en estación de trabajo HR-042",
            severity="critical",
            status="investigating",
            source="EDR",
            assigned_to="admin",
        ),
        Incident(
            title="Exfiltración de datos sospechosa",
            description="Transferencia anómala de 2.3GB hacia IP externa",
            severity="critical",
            status="open",
            source="DLP",
            assigned_to="analyst",
        ),
        Incident(
            title="Phishing reportado por usuario",
            description="Email de suplantación de identidad del CEO",
            severity="medium",
            status="resolved",
            source="Email Gateway",
            assigned_to="analyst",
        ),
        Incident(
            title="Escalada de privilegios detectada",
            description="Usuario estándar ejecutó comandos de administrador",
            severity="high",
            status="open",
            source="EDR",
            assigned_to="admin",
        ),
    ]
    db.session.add_all(incidents)

    iocs = [
        IOC(
            value="192.168.1.100",
            ioc_type="ip",
            risk_score=85,
            verdict="malicious",
            blocked=True,
            source="Threat Intel",
        ),
        IOC(
            value="10.0.0.55",
            ioc_type="ip",
            risk_score=45,
            verdict="suspicious",
            blocked=False,
            source="SIEM",
        ),
        IOC(
            value="a1b2c3d4e5f6789012345678901234567890abcd",
            ioc_type="sha1",
            risk_score=92,
            verdict="malicious",
            blocked=True,
            source="VirusTotal",
        ),
        IOC(
            value="8.8.8.8",
            ioc_type="ip",
            risk_score=5,
            verdict="clean",
            blocked=False,
            source="Manual",
        ),
    ]
    db.session.add_all(iocs)

    vulnerabilities = [
        Vulnerability(
            cve_id="CVE-2024-3400",
            title="Palo Alto PAN-OS Command Injection",
            severity="critical",
            cvss_score=10.0,
            is_kev=True,
            affected_systems="Firewall PA-5200",
            status="open",
        ),
        Vulnerability(
            cve_id="CVE-2023-4966",
            title="Citrix Bleed - Information Disclosure",
            severity="critical",
            cvss_score=9.4,
            is_kev=True,
            affected_systems="Citrix NetScaler ADC",
            status="in_progress",
        ),
        Vulnerability(
            cve_id="CVE-2024-21413",
            title="Microsoft Outlook MonikerLink RCE",
            severity="high",
            cvss_score=9.8,
            is_kev=True,
            affected_systems="Microsoft Outlook",
            status="open",
        ),
        Vulnerability(
            cve_id="CVE-2023-44487",
            title="HTTP/2 Rapid Reset Attack",
            severity="high",
            cvss_score=7.5,
            is_kev=False,
            affected_systems="Web Servers",
            status="mitigated",
        ),
        Vulnerability(
            cve_id="CVE-2024-1086",
            title="Linux Kernel Use-After-Free",
            severity="high",
            cvss_score=7.8,
            is_kev=True,
            affected_systems="Linux Servers",
            status="open",
        ),
    ]
    db.session.add_all(vulnerabilities)

    now = datetime.now(timezone.utc)
    audit_logs = [
        AuditLog(
            user_id=1,
            username="admin",
            action="Playbook ejecutado: Aislar Host",
            details="Host WS-HR-042 aislado de la red",
            created_at=now - timedelta(minutes=15),
        ),
        AuditLog(
            user_id=2,
            username="analyst",
            action="IOC enriquecido y bloqueado",
            details="IP 192.168.1.100 marcada como maliciosa",
            created_at=now - timedelta(minutes=45),
        ),
        AuditLog(
            user_id=2,
            username="analyst",
            action="Incidente actualizado",
            details="INC-001 cambiado a estado 'investigating'",
            created_at=now - timedelta(hours=2),
        ),
        AuditLog(
            user_id=1,
            username="admin",
            action="Usuario registrado",
            details="Nuevo analista creado en el sistema",
            created_at=now - timedelta(hours=5),
        ),
        AuditLog(
            user_id=2,
            username="analyst",
            action="Vulnerabilidad KEV revisada",
            details="CVE-2024-3400 asignada para parcheo urgente",
            created_at=now - timedelta(hours=8),
        ),
    ]
    db.session.add_all(audit_logs)

    db.session.commit()

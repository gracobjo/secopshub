from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="analyst")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    mfa_secret = db.Column(db.String(64), nullable=True)
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=False)
    auth_source = db.Column(db.String(20), nullable=False, default="local")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "mfa_enabled": self.mfa_enabled,
            "auth_source": self.auth_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AppSetting(db.Model):
    __tablename__ = "app_settings"

    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")
    source = db.Column(db.String(100))
    assigned_to = db.Column(db.String(80))
    external_id = db.Column(db.String(128), unique=True, nullable=True, index=True)
    src_ip = db.Column(db.String(64), nullable=True)
    hostname = db.Column(db.String(200), nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "source": self.source,
            "assigned_to": self.assigned_to,
            "external_id": self.external_id,
            "src_ip": self.src_ip,
            "hostname": self.hostname,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class IOC(db.Model):
    __tablename__ = "iocs"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(256), nullable=False)
    ioc_type = db.Column(db.String(20), nullable=False)
    risk_score = db.Column(db.Integer, default=0)
    verdict = db.Column(db.String(50))
    blocked = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(100))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "value": self.value,
            "ioc_type": self.ioc_type,
            "risk_score": self.risk_score,
            "verdict": self.verdict,
            "blocked": self.blocked,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Vulnerability(db.Model):
    __tablename__ = "vulnerabilities"

    id = db.Column(db.Integer, primary_key=True)
    cve_id = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(300), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    cvss_score = db.Column(db.Float)
    is_kev = db.Column(db.Boolean, default=False)
    affected_systems = db.Column(db.Text)
    status = db.Column(db.String(30), default="open")
    discovered_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cve_id": self.cve_id,
            "title": self.title,
            "severity": self.severity,
            "cvss_score": self.cvss_score,
            "is_kev": self.is_kev,
            "affected_systems": self.affected_systems,
            "status": self.status,
            "discovered_at": self.discovered_at.isoformat()
            if self.discovered_at
            else None,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    username = db.Column(db.String(80))
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PlaybookApproval(db.Model):
    """Solicitud de ejecución con aprobación 4-eyes."""

    __tablename__ = "playbook_approvals"

    id = db.Column(db.Integer, primary_key=True)
    playbook_id = db.Column(db.String(50), nullable=False)
    params_json = db.Column(db.Text, nullable=False, default="{}")
    status = db.Column(db.String(20), nullable=False, default="pending")
    # pending | approved | rejected | executed | failed
    requested_by = db.Column(db.String(80), nullable=False)
    requested_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    approved_by = db.Column(db.String(80))
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    result_json = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    resolved_at = db.Column(db.DateTime)

    def to_dict(self) -> dict:
        import json

        try:
            params = json.loads(self.params_json or "{}")
        except json.JSONDecodeError:
            params = {}
        try:
            result = json.loads(self.result_json) if self.result_json else None
        except json.JSONDecodeError:
            result = None
        return {
            "id": self.id,
            "playbook_id": self.playbook_id,
            "params": params,
            "status": self.status,
            "requested_by": self.requested_by,
            "approved_by": self.approved_by,
            "result": result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

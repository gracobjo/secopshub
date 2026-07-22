"""Initial schema baseline for SecOps Hub

Revision ID: 001_initial
Revises:
Create Date: 2026-07-22
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("email", sa.String(120), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("mfa_secret", sa.String(64), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auth_source", sa.String(20), nullable=False, server_default="local"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("assigned_to", sa.String(80), nullable=True),
        sa.Column("external_id", sa.String(128), nullable=True),
        sa.Column("src_ip", sa.String(64), nullable=True),
        sa.Column("hostname", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_incidents_external_id", "incidents", ["external_id"], unique=True)

    op.create_table(
        "iocs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("value", sa.String(256), nullable=False),
        sa.Column("ioc_type", sa.String(20), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("verdict", sa.String(50), nullable=True),
        sa.Column("blocked", sa.Boolean(), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "vulnerabilities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cve_id", sa.String(20), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("is_kev", sa.Boolean(), nullable=True),
        sa.Column("affected_systems", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=True),
        sa.Column("discovered_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("username", sa.String(80), nullable=True),
        sa.Column("action", sa.String(200), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("audit_logs")
    op.drop_table("vulnerabilities")
    op.drop_table("iocs")
    op.drop_index("ix_incidents_external_id", table_name="incidents")
    op.drop_table("incidents")
    op.drop_table("users")

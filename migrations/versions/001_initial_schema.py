"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-26

"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("image_visible", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "allowed_emails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_allowed_emails_email", "allowed_emails", ["email"])
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_admins_email", "admins", ["email"])
    op.create_table(
        "yale_students",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("year", sa.String(length=10), nullable=True),
        sa.Column("netid", sa.String(length=50), nullable=True),
        sa.Column("birthday", sa.String(length=50), nullable=True),
        sa.Column("major", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("email"),
    )
    op.create_table(
        "scan_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_logs_email", "scan_logs", ["email"])
    op.create_index("ix_scan_logs_scanned_at", "scan_logs", ["scanned_at"])


def downgrade():
    op.drop_index("ix_scan_logs_scanned_at", table_name="scan_logs")
    op.drop_index("ix_scan_logs_email", table_name="scan_logs")
    op.drop_table("scan_logs")
    op.drop_table("yale_students")
    op.drop_index("ix_admins_email", table_name="admins")
    op.drop_table("admins")
    op.drop_index("ix_allowed_emails_email", table_name="allowed_emails")
    op.drop_table("allowed_emails")
    op.drop_table("event_settings")

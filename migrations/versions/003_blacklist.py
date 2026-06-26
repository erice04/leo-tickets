"""Add blacklisted_emails table

Revision ID: 003_blacklist
Revises: 002_rbac
Create Date: 2026-06-26

"""
from alembic import op
import sqlalchemy as sa

revision = "003_blacklist"
down_revision = "002_rbac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "blacklisted_emails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_blacklisted_emails_email", "blacklisted_emails", ["email"])


def downgrade():
    op.drop_index("ix_blacklisted_emails_email", table_name="blacklisted_emails")
    op.drop_table("blacklisted_emails")

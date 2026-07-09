"""Add default_theme to event_settings

Revision ID: 007_default_theme
Revises: 006_watermark
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "007_default_theme"
down_revision = "006_watermark"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "default_theme",
            sa.String(length=8),
            nullable=False,
            server_default="light",
        ),
    )
    op.alter_column("event_settings", "default_theme", server_default=None)


def downgrade():
    op.drop_column("event_settings", "default_theme")

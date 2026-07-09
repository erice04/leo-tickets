"""Remove ticket_logo_opacity; logo is embedded in QR center

Revision ID: 008_embed_logo
Revises: 007_default_theme
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "008_embed_logo"
down_revision = "007_default_theme"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("event_settings", "ticket_logo_opacity")


def downgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "ticket_logo_opacity",
            sa.Float(),
            nullable=False,
            server_default="0.2",
        ),
    )
    op.alter_column("event_settings", "ticket_logo_opacity", server_default=None)

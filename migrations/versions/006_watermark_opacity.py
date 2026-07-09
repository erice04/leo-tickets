"""Watermark opacity and custom image upload

Revision ID: 006_watermark
Revises: 005_ticket_logo
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "006_watermark"
down_revision = "005_ticket_logo"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "ticket_logo_opacity",
            sa.Float(),
            nullable=False,
            server_default="0.2",
        ),
    )
    op.add_column(
        "event_settings",
        sa.Column("watermark_image", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "event_settings",
        sa.Column("watermark_content_type", sa.String(length=64), nullable=True),
    )
    op.execute(
        """
        UPDATE event_settings
        SET ticket_logo_opacity = CASE
            WHEN ticket_logo_visible THEN 0.2
            ELSE 0
        END
        """
    )
    op.drop_column("event_settings", "ticket_logo_visible")
    op.alter_column("event_settings", "ticket_logo_opacity", server_default=None)


def downgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "ticket_logo_visible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.execute(
        """
        UPDATE event_settings
        SET ticket_logo_visible = (ticket_logo_opacity > 0)
        """
    )
    op.drop_column("event_settings", "watermark_content_type")
    op.drop_column("event_settings", "watermark_image")
    op.drop_column("event_settings", "ticket_logo_opacity")
    op.alter_column("event_settings", "ticket_logo_visible", server_default=None)

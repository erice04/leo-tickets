"""Default watermark_preset to none

Revision ID: 014_watermark_preset_none
Revises: 013_postcard_stamp_preset
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "014_watermark_preset_none"
down_revision = "013_postcard_stamp_preset"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE event_settings
        SET watermark_preset = 'none'
        WHERE watermark_preset = 'leo'
          AND watermark_image IS NULL
        """
    )
    op.alter_column(
        "event_settings",
        "watermark_preset",
        server_default="none",
    )


def downgrade():
    op.alter_column(
        "event_settings",
        "watermark_preset",
        server_default="leo",
    )

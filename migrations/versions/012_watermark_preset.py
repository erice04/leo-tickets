"""Add watermark_preset to event_settings

Revision ID: 012_watermark_preset
Revises: 011_postcard_stamp_orientation
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "012_watermark_preset"
down_revision = "011_postcard_stamp_orientation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "watermark_preset",
            sa.String(length=16),
            nullable=False,
            server_default="leo",
        ),
    )
    op.alter_column("event_settings", "watermark_preset", server_default=None)


def downgrade():
    op.drop_column("event_settings", "watermark_preset")

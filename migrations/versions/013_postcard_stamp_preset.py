"""Add postcard_stamp_preset to event_settings

Revision ID: 013_postcard_stamp_preset
Revises: 012_watermark_preset
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "013_postcard_stamp_preset"
down_revision = "012_watermark_preset"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "postcard_stamp_preset",
            sa.String(length=24),
            nullable=False,
            server_default="sterling",
        ),
    )
    op.alter_column("event_settings", "postcard_stamp_preset", server_default=None)


def downgrade():
    op.drop_column("event_settings", "postcard_stamp_preset")

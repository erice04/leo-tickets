"""Add postcard_stamp_orientation to event_settings

Revision ID: 011_postcard_stamp_orientation
Revises: 010_postcard_stamp_default
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "011_postcard_stamp_orientation"
down_revision = "010_postcard_stamp_default"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "postcard_stamp_orientation",
            sa.String(length=16),
            nullable=False,
            server_default="vertical",
        ),
    )
    op.alter_column("event_settings", "postcard_stamp_orientation", server_default=None)


def downgrade():
    op.drop_column("event_settings", "postcard_stamp_orientation")

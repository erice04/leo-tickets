"""Add postcard_stamp_default to event_settings

Revision ID: 010_postcard_stamp_default
Revises: 009_postcard
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "010_postcard_stamp_default"
down_revision = "009_postcard"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "postcard_stamp_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("event_settings", "postcard_stamp_default", server_default=None)


def downgrade():
    op.drop_column("event_settings", "postcard_stamp_default")

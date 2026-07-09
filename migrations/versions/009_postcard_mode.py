"""Add postcard_enabled to event_settings

Revision ID: 009_postcard
Revises: 008_embed_logo
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "009_postcard"
down_revision = "008_embed_logo"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "postcard_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("event_settings", "postcard_enabled", server_default=None)


def downgrade():
    op.drop_column("event_settings", "postcard_enabled")

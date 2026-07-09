"""Add ticket_logo_visible to event_settings

Revision ID: 005_ticket_logo
Revises: 004_contact_email
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "005_ticket_logo"
down_revision = "004_contact_email"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "ticket_logo_visible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.alter_column("event_settings", "ticket_logo_visible", server_default=None)


def downgrade():
    op.drop_column("event_settings", "ticket_logo_visible")

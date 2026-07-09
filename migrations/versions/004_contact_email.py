"""Add contact_email to event_settings

Revision ID: 004_contact_email
Revises: 003_blacklist
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa

revision = "004_contact_email"
down_revision = "003_blacklist"
branch_labels = None
depends_on = None

DEFAULT_CONTACT_EMAIL = "leosocialchairs@gmail.com"


def upgrade():
    op.add_column(
        "event_settings",
        sa.Column(
            "contact_email",
            sa.String(length=255),
            nullable=False,
            server_default=DEFAULT_CONTACT_EMAIL,
        ),
    )
    op.alter_column("event_settings", "contact_email", server_default=None)


def downgrade():
    op.drop_column("event_settings", "contact_email")

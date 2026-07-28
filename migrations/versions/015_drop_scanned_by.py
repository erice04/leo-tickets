"""Drop unused scan_logs.scanned_by column

scanned_by was only ever written by the /scanner_result and /api/v1/scans
handlers, and only when a caller authenticated via Google session rather
than the scanner kiosk API key (the normal, documented deployment always
configures SCANNER_API_KEY, so that branch resolves to NULL in practice).
Nothing in the codebase ever reads, filters, or displays the column, so it
is dead write-only data.

Revision ID: 015_drop_scanned_by
Revises: 014_watermark_preset_none
Create Date: 2026-07-28

"""
from alembic import op
import sqlalchemy as sa

revision = "015_drop_scanned_by"
down_revision = "014_watermark_preset_none"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("scan_logs", "scanned_by")


def downgrade():
    op.add_column("scan_logs", sa.Column("scanned_by", sa.String(length=255), nullable=True))

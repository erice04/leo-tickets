"""Functional indexes on LOWER(email) for scan_logs and yale_students

The analytics service joins scan_logs to yale_students on
LOWER(email) = LOWER(email) for case-insensitive matching. A plain btree
index on email can't be used to satisfy that join efficiently at scale, so
add expression indexes on lower(email) for both tables.

Revision ID: 016_email_lower_indexes
Revises: 015_drop_scanned_by
Create Date: 2026-07-28

"""
from alembic import op

revision = "016_email_lower_indexes"
down_revision = "015_drop_scanned_by"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE INDEX ix_scan_logs_email_lower ON scan_logs (LOWER(email))"
    )
    op.execute(
        "CREATE INDEX ix_yale_students_email_lower ON yale_students (LOWER(email))"
    )


def downgrade():
    op.execute("DROP INDEX ix_scan_logs_email_lower")
    op.execute("DROP INDEX ix_yale_students_email_lower")

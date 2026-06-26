"""RBAC users and role assignments

Revision ID: 002_rbac
Revises: 001_initial
Create Date: 2026-06-26

"""
from alembic import op
import sqlalchemy as sa

revision = "002_rbac"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "role_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role", name="uq_user_role"),
    )

    op.add_column("scan_logs", sa.Column("scanned_by", sa.String(length=255), nullable=True))

    # Migrate legacy admins table if it exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "admins" in inspector.get_table_names():
        admins = bind.execute(sa.text("SELECT email FROM admins")).fetchall()
        for (email,) in admins:
            normalized = email.strip().lower()
            user_id = bind.execute(
                sa.text("INSERT INTO users (email, is_active, created_at, updated_at) VALUES (:email, true, NOW(), NOW()) RETURNING id"),
                {"email": normalized},
            ).scalar()
            bind.execute(
                sa.text("INSERT INTO role_assignments (user_id, role) VALUES (:user_id, 'admin')"),
                {"user_id": user_id},
            )
        op.drop_index("ix_admins_email", table_name="admins")
        op.drop_table("admins")


def downgrade():
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_admins_email", "admins", ["email"])

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT u.email FROM users u "
            "JOIN role_assignments r ON r.user_id = u.id "
            "WHERE r.role = 'admin'"
        )
    ).fetchall()
    for (email,) in rows:
        bind.execute(sa.text("INSERT INTO admins (email) VALUES (:email)"), {"email": email})

    op.drop_column("scan_logs", "scanned_by")
    op.drop_table("role_assignments")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

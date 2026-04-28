"""add reports and user roles

Revision ID: a7c2d9e4f6b1
Revises: f1e2d3c4b5a6
Create Date: 2026-04-28 21:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a7c2d9e4f6b1"
down_revision: Union[str, Sequence[str], None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "role" not in user_columns:
        op.add_column(
            "users",
            sa.Column("role", sa.String(), server_default="user", nullable=True),
        )

    if not inspector.has_table("reports"):
        op.create_table(
            "reports",
            sa.Column("report_id", sa.UUID(), nullable=False),
            sa.Column("reporter_id", sa.UUID(), nullable=False),
            sa.Column("entity_type", sa.String(length=20), nullable=False),
            sa.Column("entity_id", sa.UUID(), nullable=False),
            sa.Column("reason", sa.String(length=500), nullable=False),
            sa.Column(
                "status",
                sa.String(length=20),
                server_default="open",
                nullable=False,
            ),
            sa.Column("reviewed_by", sa.UUID(), nullable=True),
            sa.Column(
                "reviewed_at",
                postgresql.TIMESTAMP(timezone=True),
                nullable=True,
            ),
            sa.Column("resolution_note", sa.String(length=500), nullable=True),
            sa.Column(
                "created_at",
                postgresql.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(
                ["reporter_id"],
                ["users.user_id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["reviewed_by"],
                ["users.user_id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("report_id"),
        )

    report_indexes = {index["name"] for index in inspector.get_indexes("reports")}
    if "ix_reports_status_created_at" not in report_indexes:
        op.create_index(
            "ix_reports_status_created_at",
            "reports",
            ["status", "created_at"],
            unique=False,
        )
    if "ix_reports_entity" not in report_indexes:
        op.create_index(
            "ix_reports_entity",
            "reports",
            ["entity_type", "entity_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("reports"):
        report_indexes = {index["name"] for index in inspector.get_indexes("reports")}
        if "ix_reports_entity" in report_indexes:
            op.drop_index("ix_reports_entity", table_name="reports")
        if "ix_reports_status_created_at" in report_indexes:
            op.drop_index("ix_reports_status_created_at", table_name="reports")
        op.drop_table("reports")

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "role" in user_columns:
        op.drop_column("users", "role")

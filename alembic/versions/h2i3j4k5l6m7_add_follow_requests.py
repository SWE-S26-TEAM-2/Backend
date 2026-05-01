"""add follow_requests table

Revision ID: h2i3j4k5l6m7
Revises: f1a2b3c4d5e6
Create Date: 2026-05-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "h2i3j4k5l6m7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("follow_requests"):
        op.create_table(
            "follow_requests",
            sa.Column(
                "request_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "requester_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "target_id",
                postgresql.UUID(as_uuid=True),
                nullable=False,
            ),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(
                ["requester_id"], ["users.user_id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["target_id"], ["users.user_id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("request_id"),
            sa.UniqueConstraint(
                "requester_id", "target_id", name="uq_follow_request"
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("follow_requests"):
        op.drop_table("follow_requests")

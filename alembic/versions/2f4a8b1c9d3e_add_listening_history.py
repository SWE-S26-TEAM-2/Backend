"""add listening history

Revision ID: 2f4a8b1c9d3e
Revises: 9e7f5d4c2b1a
Create Date: 2026-04-13 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2f4a8b1c9d3e"
down_revision: Union[str, Sequence[str], None] = "9e7f5d4c2b1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "listening_history",
        sa.Column("history_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("track_id", sa.UUID(), nullable=False),
        sa.Column("duration_listened_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "played_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.track_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("history_id"),
    )
    op.create_index(
        "ix_listening_history_user_id_played_at",
        "listening_history",
        ["user_id", "played_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_listening_history_user_id_played_at",
        table_name="listening_history",
    )
    op.drop_table("listening_history")

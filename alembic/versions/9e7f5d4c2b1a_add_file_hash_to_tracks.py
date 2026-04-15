"""add file hash to tracks

Revision ID: 9e7f5d4c2b1a
Revises: c4d4f35c3e7e
Create Date: 2026-04-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9e7f5d4c2b1a"
down_revision: Union[str, Sequence[str], None] = "c4d4f35c3e7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tracks", sa.Column("file_hash", sa.String(), nullable=True))
    op.create_index(
        "ix_tracks_user_id_file_hash",
        "tracks",
        ["user_id", "file_hash"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_tracks_user_id_file_hash", table_name="tracks")
    op.drop_column("tracks", "file_hash")

"""finish module4 track metadata

Revision ID: 7b8c9d0e1f2a
Revises: 2f4a8b1c9d3e
Create Date: 2026-04-13 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7b8c9d0e1f2a"
down_revision: Union[str, Sequence[str], None] = "2f4a8b1c9d3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tracks", sa.Column("genre", sa.String(), nullable=True))
    op.add_column("tracks", sa.Column("tags", sa.JSON(), nullable=True))
    op.add_column("tracks", sa.Column("release_date", sa.Date(), nullable=True))
    op.add_column(
        "tracks",
        sa.Column(
            "processing_status",
            sa.String(),
            server_default="finished",
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tracks", "processing_status")
    op.drop_column("tracks", "release_date")
    op.drop_column("tracks", "tags")
    op.drop_column("tracks", "genre")

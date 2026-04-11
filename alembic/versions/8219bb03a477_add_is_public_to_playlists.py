"""add is_public to playlists

Revision ID: 8219bb03a477
Revises: d010c81662bc
Create Date: 2026-04-11 22:00:32.351805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8219bb03a477'
down_revision: Union[str, Sequence[str], None] = 'd010c81662bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "playlists",
        sa.Column("is_public", sa.Boolean(), server_default="true", nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("playlists", "is_public")
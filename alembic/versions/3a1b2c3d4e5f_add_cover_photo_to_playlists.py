"""add cover photo to playlists

Revision ID: 3a1b2c3d4e5f
Revises: 2f4a8b1c9d3e
Create Date: 2026-04-18 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "2f4a8b1c9d3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('playlists', sa.Column('cover_photo_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('playlists', 'cover_photo_url')

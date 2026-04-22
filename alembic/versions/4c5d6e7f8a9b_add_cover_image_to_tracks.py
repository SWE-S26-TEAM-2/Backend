"""add cover image to tracks

Revision ID: 4c5d6e7f8a9b
Revises: 3a1b2c3d4e5f
Create Date: 2026-04-22 20:38:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4c5d6e7f8a9b"
down_revision: Union[str, Sequence[str], None] = "3a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tracks", sa.Column("cover_image_url", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tracks", "cover_image_url")

"""add playback fields to tracks

Revision ID: c4d4f35c3e7e
Revises: d010c81662bc
Create Date: 2026-04-12 11:11:14.174882

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c4d4f35c3e7e"
down_revision: Union[str, Sequence[str], None] = "d010c81662bc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tracks",
        sa.Column("visibility", sa.String(), server_default="public", nullable=True),
    )
    op.add_column(
        "tracks",
        sa.Column("play_count", sa.Integer(), server_default="0", nullable=True),
    )
    op.add_column(
        "tracks",
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "tracks",
        sa.Column("waveform_peaks", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tracks", "waveform_peaks")
    op.drop_column("tracks", "duration_seconds")
    op.drop_column("tracks", "play_count")
    op.drop_column("tracks", "visibility")

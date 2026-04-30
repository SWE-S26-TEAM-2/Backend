"""drop uq_track_one_album constraint

Revision ID: f1a2b3c4d5e6
Revises: e3f4a5b6c7d8
Create Date: 2026-04-30

"""

from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "uq_track_one_album", "album_tracks", type_="unique"
    )


def downgrade():
    op.create_unique_constraint(
        "uq_track_one_album", "album_tracks", ["track_id"]
    )

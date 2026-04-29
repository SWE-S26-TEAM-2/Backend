"""add albums module

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-04-29 01:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ── albums ─────────────────────────────────────────────────────────────────
    if not inspector.has_table("albums"):
        op.create_table(
            "albums",
            sa.Column("album_id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column("genre", sa.String(), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("release_date", sa.Date(), nullable=True),
            sa.Column("cover_photo_url", sa.String(), nullable=True),
            sa.Column(
                "visibility",
                sa.String(),
                server_default="public",
                nullable=True,
            ),
            sa.Column("upc", sa.String(), nullable=True),
            sa.Column("label", sa.String(), nullable=True),
            sa.Column(
                "like_count",
                sa.Integer(),
                server_default="0",
                nullable=True,
            ),
            sa.Column(
                "track_count",
                sa.Integer(),
                server_default="0",
                nullable=True,
            ),
            sa.Column(
                "created_at",
                postgresql.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.user_id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("album_id"),
        )

    if inspector.has_table("albums"):
        album_indexes = {
            index["name"] for index in inspector.get_indexes("albums")
        }
        if "ix_albums_user_id" not in album_indexes:
            op.create_index(
                "ix_albums_user_id", "albums", ["user_id"], unique=False
            )
        if "ix_albums_visibility" not in album_indexes:
            op.create_index(
                "ix_albums_visibility", "albums", ["visibility"], unique=False
            )

    # ── tracks.album_id ────────────────────────────────────────────────────────
    track_columns = {col["name"] for col in inspector.get_columns("tracks")}
    if "album_id" not in track_columns:
        op.add_column(
            "tracks",
            sa.Column("album_id", sa.UUID(), nullable=True),
        )
        op.create_foreign_key(
            "fk_tracks_album_id",
            "tracks",
            "albums",
            ["album_id"],
            ["album_id"],
            ondelete="SET NULL",
        )

    # ── album_tracks ───────────────────────────────────────────────────────────
    if not inspector.has_table("album_tracks"):
        op.create_table(
            "album_tracks",
            sa.Column("album_id", sa.UUID(), nullable=False),
            sa.Column("track_id", sa.UUID(), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["album_id"],
                ["albums.album_id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["track_id"],
                ["tracks.track_id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("album_id", "track_id"),
            sa.UniqueConstraint("track_id", name="uq_track_one_album"),
        )

    # ── album_likes ────────────────────────────────────────────────────────────
    if not inspector.has_table("album_likes"):
        op.create_table(
            "album_likes",
            sa.Column("album_like_id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("album_id", sa.UUID(), nullable=False),
            sa.Column(
                "created_at",
                postgresql.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(
                ["album_id"],
                ["albums.album_id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.user_id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("album_like_id"),
            sa.UniqueConstraint(
                "user_id", "album_id", name="uq_user_album_like"
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("album_likes"):
        op.drop_table("album_likes")

    if inspector.has_table("album_tracks"):
        op.drop_table("album_tracks")

    track_columns = {col["name"] for col in inspector.get_columns("tracks")}
    if "album_id" in track_columns:
        op.drop_constraint(
            "fk_tracks_album_id", "tracks", type_="foreignkey"
        )
        op.drop_column("tracks", "album_id")

    if inspector.has_table("albums"):
        album_indexes = {
            index["name"] for index in inspector.get_indexes("albums")
        }
        if "ix_albums_visibility" in album_indexes:
            op.drop_index("ix_albums_visibility", table_name="albums")
        if "ix_albums_user_id" in album_indexes:
            op.drop_index("ix_albums_user_id", table_name="albums")
        op.drop_table("albums")

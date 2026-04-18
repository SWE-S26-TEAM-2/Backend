"""add_missing_tables

Revision ID: d010c81662bc
Revises: 5fa292df3992
Create Date: 2026-03-23 08:52:48.494371

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d010c81662bc"
down_revision: Union[str, Sequence[str], None] = "5fa292df3992"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("jti", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked", sa.BOOLEAN(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name=op.f("refresh_tokens_user_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("refresh_tokens_pkey")),
        sa.UniqueConstraint("jti", name=op.f("refresh_tokens_jti_key")),
    )

    op.create_table(
        "social_links",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("platform", sa.VARCHAR(), nullable=False),
        sa.Column("url", sa.VARCHAR(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name=op.f("social_links_user_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("social_links_pkey")),
    )
    op.create_index(op.f("ix_social_links_id"), "social_links", ["id"], unique=False)

    op.create_table(
        "email_verifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token", sa.VARCHAR(), nullable=False),
        sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("used", sa.BOOLEAN(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("email_verifications_user_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("email_verifications_pkey")),
        sa.UniqueConstraint("token", name=op.f("email_verifications_token_key")),
    )

    op.create_table(
        "password_resets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token", sa.VARCHAR(), nullable=False),
        sa.Column("expires_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("used", sa.BOOLEAN(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name=op.f("password_resets_user_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("password_resets_pkey")),
        sa.UniqueConstraint("token", name=op.f("password_resets_token_key")),
    )

    op.create_table(
        "tracks",
        sa.Column("track_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("file_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name=op.f("tracks_user_id_fkey")
        ),
        sa.PrimaryKeyConstraint("track_id", name=op.f("tracks_pkey")),
    )

    op.create_table(
        "playlists",
        sa.Column("playlist_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"], name=op.f("playlists_user_id_fkey")
        ),
        sa.PrimaryKeyConstraint("playlist_id", name=op.f("playlists_pkey")),
    )

    op.create_table(
        "playlist_tracks",
        sa.Column("playlist_id", sa.UUID(), nullable=False),
        sa.Column("track_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["playlist_id"],
            ["playlists.playlist_id"],
            name=op.f("playlist_tracks_playlist_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.track_id"],
            name=op.f("playlist_tracks_track_id_fkey"),
        ),
        sa.PrimaryKeyConstraint(
            "playlist_id", "track_id", name=op.f("playlist_tracks_pkey")
        ),
    )

    op.create_table(
        "follows",
        sa.Column("follow_id", sa.UUID(), nullable=False),
        sa.Column("follower_id", sa.UUID(), nullable=False),
        sa.Column("following_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["follower_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("follows_follower_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["following_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("follows_following_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("follow_id", name=op.f("follows_pkey")),
    )

    op.create_table(
        "blocks",
        sa.Column("block_id", sa.UUID(), nullable=False),
        sa.Column("blocker_id", sa.UUID(), nullable=False),
        sa.Column("blocked_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["blocker_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("blocks_blocker_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["blocked_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("blocks_blocked_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("block_id", name=op.f("blocks_pkey")),
    )

    op.create_table(
        "conversations",
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("user1_id", sa.UUID(), nullable=False),
        sa.Column("user2_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user1_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("conversations_user1_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["user2_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("conversations_user2_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("conversation_id", name=op.f("conversations_pkey")),
    )

    op.create_table(
        "messages",
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("sender_id", sa.UUID(), nullable=False),
        sa.Column("receiver_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.String(), nullable=True),
        sa.Column("track_id", sa.UUID(), nullable=True),
        sa.Column("playlist_id", sa.UUID(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.conversation_id"],
            ondelete="CASCADE",
            name=op.f("messages_conversation_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("messages_sender_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["receiver_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("messages_receiver_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("message_id", name=op.f("messages_pkey")),
    )

    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("notification_type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=True),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=True),
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
            name=op.f("notifications_user_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name=op.f("notifications_actor_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("notification_id", name=op.f("notifications_pkey")),
    )

    op.create_table(
        "comments",
        sa.Column("comment_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("track_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.String(500), nullable=False),
        sa.Column("timestamp_in_track", sa.Integer(), nullable=True),
        sa.Column("parent_comment_id", sa.UUID(), nullable=True),
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
            name=op.f("comments_user_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.track_id"],
            ondelete="CASCADE",
            name=op.f("comments_track_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["parent_comment_id"],
            ["comments.comment_id"],
            ondelete="CASCADE",
            name=op.f("comments_parent_comment_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("comment_id", name=op.f("comments_pkey")),
    )

    op.create_table(
        "likes",
        sa.Column("like_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("track_id", sa.UUID(), nullable=False),
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
            name=op.f("likes_user_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.track_id"],
            ondelete="CASCADE",
            name=op.f("likes_track_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("like_id", name=op.f("likes_pkey")),
        sa.UniqueConstraint("user_id", "track_id", name="uq_user_track_like"),
    )

    op.create_table(
        "reposts",
        sa.Column("repost_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("track_id", sa.UUID(), nullable=False),
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
            name=op.f("reposts_user_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.track_id"],
            ondelete="CASCADE",
            name=op.f("reposts_track_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("repost_id", name=op.f("reposts_pkey")),
        sa.UniqueConstraint("user_id", "track_id", name="uq_user_track_repost"),
    )

    op.create_table(
        "playlist_likes",
        sa.Column("playlist_like_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("playlist_id", sa.UUID(), nullable=False),
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
            name=op.f("playlist_likes_user_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["playlist_id"],
            ["playlists.playlist_id"],
            ondelete="CASCADE",
            name=op.f("playlist_likes_playlist_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("playlist_like_id", name=op.f("playlist_likes_pkey")),
        sa.UniqueConstraint("user_id", "playlist_id", name="uq_user_playlist_like"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("playlist_likes")
    op.drop_table("reposts")
    op.drop_table("likes")
    op.drop_table("comments")
    op.drop_table("notifications")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("blocks")
    op.drop_table("follows")
    op.drop_table("playlist_tracks")
    op.drop_table("playlists")
    op.drop_table("tracks")
    op.drop_table("password_resets")
    op.drop_table("email_verifications")
    op.drop_index(op.f("ix_social_links_id"), table_name="social_links")
    op.drop_table("social_links")
    op.drop_table("refresh_tokens")

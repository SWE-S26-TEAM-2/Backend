import uuid

from sqlalchemy import Column, ForeignKey, TIMESTAMP, text  # type: ignore
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class PlaylistLike(Base):
    __tablename__ = "playlist_likes"
    __allow_unmapped__ = True

    playlist_like_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    playlist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("playlists.playlist_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("user_id", "playlist_id", name="uq_user_playlist_like"),
    )

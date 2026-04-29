import uuid

from sqlalchemy import (  # type: ignore
    Column, ForeignKey, TIMESTAMP, text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class AlbumLike(Base):
    __tablename__ = "album_likes"
    __allow_unmapped__ = True

    album_like_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    album_id = Column(
        UUID(as_uuid=True),
        ForeignKey("albums.album_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("user_id", "album_id", name="uq_user_album_like"),
    )

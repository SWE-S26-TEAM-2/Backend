import uuid

from sqlalchemy import Column, String, Integer, TIMESTAMP  # type: ignore
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Comment(Base):
    __tablename__ = "comments"
    __allow_unmapped__ = True

    comment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracks.track_id", ondelete="CASCADE"),
        nullable=False,
    )
    content = Column(String(500), nullable=False)
    timestamp_in_track = Column(Integer, nullable=True)
    parent_comment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("comments.comment_id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

import uuid

from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP, text  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class ListeningHistory(Base):
    __tablename__ = "listening_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    duration_listened_seconds = Column(Integer, nullable=True)
    played_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

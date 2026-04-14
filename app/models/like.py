import uuid

from sqlalchemy import Column, TIMESTAMP, ForeignKey, text  # type: ignore
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Like(Base):
    __tablename__ = "likes"
    __allow_unmapped__ = True

    like_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="uq_user_track_like"),
    )

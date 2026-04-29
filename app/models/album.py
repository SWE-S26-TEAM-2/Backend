import uuid
from sqlalchemy import (  # type: ignore
    Column, String, Integer, Date, JSON, TIMESTAMP, text, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Album(Base):
    __tablename__ = "albums"

    album_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    release_date = Column(Date, nullable=True)
    cover_photo_url = Column(String, nullable=True)
    visibility = Column(String, server_default="public")
    upc = Column(String, nullable=True)
    label = Column(String, nullable=True)
    like_count = Column(Integer, server_default="0")
    track_count = Column(Integer, server_default="0")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

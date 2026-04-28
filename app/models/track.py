import uuid
from sqlalchemy import (  # type: ignore
    JSON,
    Column,
    Date,
    Integer,
    String,
    ForeignKey,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Track(Base):
    __tablename__ = "tracks"

    track_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    genre = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)
    release_date = Column(Date, nullable=True)
    file_url = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)
    visibility = Column(String, server_default="public")
    processing_status = Column(String, server_default="finished")
    play_count = Column(Integer, server_default="0")
    duration_seconds = Column(Integer, nullable=True)
    waveform_peaks = Column(JSON, nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=True
    )

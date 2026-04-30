from sqlalchemy import Column, Integer, ForeignKey  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class AlbumTrack(Base):
    __tablename__ = "album_tracks"

    album_id = Column(
        UUID(as_uuid=True),
        ForeignKey("albums.album_id", ondelete="CASCADE"),
        primary_key=True,
    )
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracks.track_id", ondelete="CASCADE"),
        primary_key=True,
    )
    position = Column(Integer, nullable=False, default=1)

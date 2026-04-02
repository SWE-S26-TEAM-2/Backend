from sqlalchemy import Column, ForeignKey  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    playlist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("playlists.playlist_id"),
        primary_key=True,
    )
    track_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tracks.track_id"),
        primary_key=True,
    )
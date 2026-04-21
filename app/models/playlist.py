import uuid
from sqlalchemy import Column, String, ForeignKey  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Playlist(Base):
    __tablename__ = "playlists"

    playlist_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    cover_photo_url = Column(String, nullable=True)

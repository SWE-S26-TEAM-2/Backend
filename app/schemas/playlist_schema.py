from typing import Optional
from pydantic import BaseModel


class CreatePlaylistRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdatePlaylistRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_photo_url: Optional[str] = None


class PlaylistTrackRequest(BaseModel):
    track_id: str

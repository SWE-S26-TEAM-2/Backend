from typing import Optional
from pydantic import BaseModel


class CreatePlaylistRequest(BaseModel):
    name: str
    is_public: Optional[bool] = True


class UpdatePlaylistRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class PlaylistTrackRequest(BaseModel):
    track_id: str

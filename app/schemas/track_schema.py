from typing import Optional
from pydantic import BaseModel


class CreateTrackRequest(BaseModel):
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    visibility: Optional[str] = None

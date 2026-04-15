from datetime import date
from typing import Optional
from pydantic import BaseModel


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[list[str]] = None
    release_date: Optional[date] = None
    file_url: Optional[str] = None
    visibility: Optional[str] = None


class RecordPlayRequest(BaseModel):
    duration_listened_seconds: Optional[int] = None

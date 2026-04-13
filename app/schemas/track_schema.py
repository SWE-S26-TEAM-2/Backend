from typing import Optional
from pydantic import BaseModel


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    visibility: Optional[str] = None


class RecordPlayRequest(BaseModel):
    duration_listened_seconds: Optional[int] = None

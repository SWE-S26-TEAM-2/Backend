from datetime import date
from typing import List, Optional

from pydantic import BaseModel, field_validator


ALLOWED_VISIBILITIES = {"public", "private"}


class CreateAlbumRequest(BaseModel):
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[str]] = None
    release_date: Optional[date] = None
    visibility: str = "public"
    upc: Optional[str] = None
    label: Optional[str] = None
    track_ids: Optional[List[str]] = None

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v: str) -> str:
        if v not in ALLOWED_VISIBILITIES:
            raise ValueError("Visibility must be 'public' or 'private'")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title cannot exceed 255 characters")
        return v

    @field_validator("upc")
    @classmethod
    def validate_upc(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not v.isdigit():
                raise ValueError("UPC must contain only digits")
            if v and len(v) not in (12, 13):
                raise ValueError("UPC must be 12 or 13 digits")
        return v


class UpdateAlbumRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[str]] = None
    release_date: Optional[date] = None
    visibility: Optional[str] = None
    upc: Optional[str] = None
    label: Optional[str] = None

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_VISIBILITIES:
            raise ValueError("Visibility must be 'public' or 'private'")
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty")
            if len(v) > 255:
                raise ValueError("Title cannot exceed 255 characters")
        return v


class AlbumTrackRequest(BaseModel):
    track_id: str
    position: Optional[int] = None


class ReorderAlbumTracksRequest(BaseModel):
    track_ids: List[str]

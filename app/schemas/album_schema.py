from typing import List, Optional

from pydantic import BaseModel, field_validator


class CreateAlbumRequest(BaseModel):
    title: str
    year: int
    track_ids: Optional[List[str]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title cannot exceed 255 characters")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 1900 or v > 2100:
            raise ValueError("Year must be between 1900 and 2100")
        return v


class UpdateAlbumRequest(BaseModel):
    title: Optional[str] = None
    year: Optional[int] = None

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

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1900 or v > 2100):
            raise ValueError("Year must be between 1900 and 2100")
        return v


class AlbumTrackRequest(BaseModel):
    track_id: str
    position: Optional[int] = None


class ReorderAlbumTracksRequest(BaseModel):
    track_ids: List[str]

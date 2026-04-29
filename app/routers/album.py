from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user, get_optional_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.album_schema import (
    AlbumTrackRequest,
    CreateAlbumRequest,
    ReorderAlbumTracksRequest,
    UpdateAlbumRequest,
)
from app.schemas.responses import (  # type: ignore
    AlbumCoverResponse,
    AlbumDetailResponse,
    AlbumLikeResponse,
    AlbumListResponse,
    AlbumResponse,
    AlbumUpdateResponse,
    MessageResponse,
)
from app.services.album_service import AlbumService

router = APIRouter(prefix="/albums", tags=["Albums"])


@router.post("/", response_model=AlbumResponse)
def create_album(
    data: CreateAlbumRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.create_album(db, user, data)


@router.get("/liked", response_model=AlbumListResponse)
def get_liked_albums(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.get_liked_albums(db, user)


@router.get("/{album_id}", response_model=AlbumDetailResponse)
def get_album(
    album_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return AlbumService.get_album(db, album_id, current_user)


@router.patch("/{album_id}", response_model=AlbumUpdateResponse)
def update_album(
    album_id: UUID,
    data: UpdateAlbumRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.update_album(db, user, album_id, data)


@router.delete("/{album_id}", response_model=MessageResponse)
def delete_album(
    album_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.delete_album(db, user, album_id)


@router.post("/{album_id}/cover", response_model=AlbumCoverResponse)
def upload_cover_photo(
    album_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.upload_cover_photo(db, user, album_id, file)


@router.post("/{album_id}/like", response_model=AlbumLikeResponse)
def like_album(
    album_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.like_album(db, user, album_id)


@router.delete("/{album_id}/like", response_model=MessageResponse)
def unlike_album(
    album_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.unlike_album(db, user, album_id)


@router.post("/{album_id}/tracks", response_model=MessageResponse)
def add_track_to_album(
    album_id: UUID,
    data: AlbumTrackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.add_track(db, user, album_id, data)


@router.delete("/{album_id}/tracks/{track_id}", response_model=MessageResponse)
def remove_track_from_album(
    album_id: UUID,
    track_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.remove_track(db, user, album_id, track_id)


@router.put("/{album_id}/tracks/reorder", response_model=MessageResponse)
def reorder_album_tracks(
    album_id: UUID,
    data: ReorderAlbumTracksRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AlbumService.reorder_tracks(db, user, album_id, data)

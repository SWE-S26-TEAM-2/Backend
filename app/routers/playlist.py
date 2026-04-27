from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.services.playlist_service import PlaylistService
from app.schemas.playlist_schema import (
    CreatePlaylistRequest,
    UpdatePlaylistRequest,
    PlaylistTrackRequest,
)
from app.schemas.responses import (  # type: ignore
    MessageResponse,
    PlaylistResponse,
    PlaylistListResponse,
    PlaylistDetailResponse,
    PlaylistUpdateResponse,
    PlaylistLikeResponse,
    PlaylistCoverResponse,
)

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.post("/", response_model=PlaylistResponse)
def create_playlist(
    data: CreatePlaylistRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.create_playlist(db, user, data)


@router.get("/liked", response_model=PlaylistListResponse)
def get_liked_playlists(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.get_liked_playlists(db, user)


@router.get("/{playlist_id}", response_model=PlaylistDetailResponse)
def get_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db),
):
    return PlaylistService.get_playlist(db, playlist_id)


@router.patch("/{playlist_id}", response_model=PlaylistUpdateResponse)
def update_playlist(
    playlist_id: UUID,
    data: UpdatePlaylistRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.update_playlist(db, user, playlist_id, data)


@router.delete("/{playlist_id}", response_model=MessageResponse)
def delete_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.delete_playlist(db, user, playlist_id)


@router.post("/{playlist_id}/like", response_model=PlaylistLikeResponse)
def like_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.like_playlist(db, user, playlist_id)


@router.delete("/{playlist_id}/like", response_model=MessageResponse)
def unlike_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.unlike_playlist(db, user, playlist_id)


@router.post("/{playlist_id}/cover", response_model=PlaylistCoverResponse)
def upload_cover_photo(
    playlist_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.upload_cover_photo(db, user, playlist_id, file)


@router.post("/{playlist_id}/tracks", response_model=MessageResponse)
def add_track_to_playlist(
    playlist_id: UUID,
    data: PlaylistTrackRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.add_track_to_playlist(db, user, playlist_id, data)


@router.delete("/{playlist_id}/tracks/{track_id}", response_model=MessageResponse)
def remove_track_from_playlist(
    playlist_id: UUID,
    track_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.remove_track_from_playlist(db, user, playlist_id, track_id)

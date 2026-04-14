from uuid import UUID

from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.services.playlist_service import PlaylistService
from app.schemas.playlist_schema import (
    CreatePlaylistRequest,
    UpdatePlaylistRequest,
    PlaylistTrackRequest,
)

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.post("/")
def create_playlist(
    data: CreatePlaylistRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.create_playlist(db, user, data)


@router.get("/liked")
def get_liked_playlists(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.get_liked_playlists(db, user)


@router.get("/{playlist_id}")
def get_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db),
):
    return PlaylistService.get_playlist(db, playlist_id)


@router.patch("/{playlist_id}")
def update_playlist(
    playlist_id: UUID,
    data: UpdatePlaylistRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.update_playlist(db, user, playlist_id, data)


@router.delete("/{playlist_id}")
def delete_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.delete_playlist(db, user, playlist_id)


@router.post("/{playlist_id}/like")
def like_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.like_playlist(db, user, playlist_id)


@router.delete("/{playlist_id}/like")
def unlike_playlist(
    playlist_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.unlike_playlist(db, user, playlist_id)


@router.post("/{playlist_id}/tracks")
def add_track_to_playlist(
    playlist_id: UUID,
    data: PlaylistTrackRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.add_track_to_playlist(db, user, playlist_id, data)


@router.delete("/{playlist_id}/tracks/{track_id}")
def remove_track_from_playlist(
    playlist_id: UUID,
    track_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return PlaylistService.remove_track_from_playlist(db, user, playlist_id, track_id)

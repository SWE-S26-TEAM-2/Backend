from fastapi import APIRouter, Depends, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.database.database import get_db
from app.services.search_service import SearchService
from app.schemas.responses import (  # type: ignore
    SearchUsersResponse,
    SearchTracksResponse,
    SearchPlaylistsResponse,
)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/users", response_model=SearchUsersResponse)
def search_users(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    return SearchService.search_users(db, keyword)


@router.get("/tracks", response_model=SearchTracksResponse)
def search_tracks(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    return SearchService.search_tracks(db, keyword)


@router.get("/playlists", response_model=SearchPlaylistsResponse)
def search_playlists(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    return SearchService.search_playlists(db, keyword)

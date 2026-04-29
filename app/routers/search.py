import time

from fastapi import APIRouter, Depends, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.schemas.responses import (
    SearchUsersResponse,
    SearchTracksResponse,
    SearchPlaylistsResponse,
)
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/users", response_model=SearchUsersResponse)
def search_users(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start = time.perf_counter()
    result = SearchService.search_users(db, keyword, current_user.user_id)
    result["query_time_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result


@router.get("/tracks", response_model=SearchTracksResponse)
def search_tracks(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    start = time.perf_counter()
    result = SearchService.search_tracks(db, keyword)
    result["query_time_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result


@router.get("/playlists", response_model=SearchPlaylistsResponse)
def search_playlists(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    start = time.perf_counter()
    result = SearchService.search_playlists(db, keyword)
    result["query_time_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result

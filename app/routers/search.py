import time

from fastapi import APIRouter, Depends, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.database.database import get_db
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/users")
def search_users(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    start = time.perf_counter()
    result = SearchService.search_users(db, keyword)
    result["query_time_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result


@router.get("/tracks")
def search_tracks(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    start = time.perf_counter()
    result = SearchService.search_tracks(db, keyword)
    result["query_time_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result


@router.get("/playlists")
def search_playlists(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    start = time.perf_counter()
    result = SearchService.search_playlists(db, keyword)
    result["query_time_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result

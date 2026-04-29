import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.schemas.responses import FeedResponse
from app.services.feed_service import FeedService

router = APIRouter(prefix="/feed", tags=["Feed"])


@router.get("/following", response_model=FeedResponse)
def get_following_feed(
    limit: int = Query(20, ge=1, le=50, description="Number of tracks per page"),
    cursor: str | None = Query(
        None, description="Pagination cursor returned by the previous response"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start = time.perf_counter()
    result = FeedService.get_following_feed(db, current_user, limit, cursor)
    result["query_time_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result


@router.get("/discover", response_model=FeedResponse)
def get_discover_feed(
    limit: int = Query(20, ge=1, le=50, description="Number of tracks per page"),
    cursor: str | None = Query(
        None, description="Pagination cursor returned by the previous response"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    start = time.perf_counter()
    result = FeedService.get_discover_feed(db, current_user, limit, cursor)
    result["query_time_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result

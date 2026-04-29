"""
Feed Caching Performance Comparison — Optimized Endpoint.

The original /feed/discover is the "before" baseline — hits the DB every time.
This endpoint is the "after" — same logic, but result is cached for 60 seconds.

Compare:
  GET /feed/discover                  ← original (no cache, DB hit every time)
  GET /feed/cached/discover/optimized ← with in-memory cache (instant after first call)

Response includes query_time_ms and cache_hit so you can see the difference.
Hit /feed/cached/discover/optimized twice: first call is slow (cache MISS),
second call within 60s is instant (cache HIT).
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.cache import feed_cache, cache_get, cache_set, cache_get_timestamp
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.repositories.feed_repo import FeedRepository
from app.services.feed_service import FeedService, _EMPTY_STATS

router = APIRouter(prefix="/feed/cached", tags=["Feed Caching (Optimized)"])


def _build_discover_result(db: Session, user, limit: int, cursor: str | None) -> dict:
    offset = 0
    if cursor:
        try:
            offset = int(cursor)
        except ValueError:
            pass

    top_genres = FeedRepository.get_user_top_genres(db, user.user_id)
    heard_ids = FeedRepository.get_heard_track_ids(db, user.user_id)
    blocked_ids = FeedRepository.get_blocked_ids(db, user.user_id)

    if top_genres:
        rows = FeedRepository.get_tracks_by_genres(
            db, top_genres, heard_ids, blocked_ids, limit, offset
        )
        if len(rows) < limit:
            seen_ids = heard_ids | {t.track_id for t, _ in rows}
            rows += FeedRepository.get_trending_tracks(
                db, seen_ids, blocked_ids, limit - len(rows), 0
            )
    else:
        rows = FeedRepository.get_trending_tracks(
            db, heard_ids, blocked_ids, limit, offset
        )

    if not rows:
        return {"items": [], "next_cursor": None, "has_more": False}

    track_ids = [track.track_id for track, _ in rows]
    stats_map = FeedRepository.get_engagement_stats(db, track_ids, user.user_id)

    items = [
        FeedService._serialize_item(
            track, artist, stats_map.get(track.track_id, _EMPTY_STATS)
        )
        for track, artist in rows
    ]

    has_more = len(items) == limit
    next_cursor = str(offset + len(items)) if has_more else None

    return {"items": items, "next_cursor": next_cursor, "has_more": has_more}


@router.get("/discover/optimized")
def get_discover_cached(
    limit: int = Query(20, ge=1, le=50),
    cursor: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Discover feed with in-memory cache (60s TTL).
    First call hits the DB. Every call within 60s after that is instant.
    Compare against GET /feed/discover which hits the DB every time.
    """
    cache_key = f"discover:{current_user.user_id}:{limit}:{cursor}"

    cached = cache_get(feed_cache, cache_key)

    if cached is not None:
        cached_at_ts = cache_get_timestamp(cache_key)
        cached_at = (
            datetime.fromtimestamp(cached_at_ts, tz=timezone.utc).isoformat()
            if cached_at_ts
            else None
        )
        return {
            "success": True,
            "optimized": True,
            "cache_hit": True,
            "query_time_ms": 0,
            "cached_at": cached_at,
            "cache_ttl_seconds": 60,
            "data": cached,
        }

    start = time.perf_counter()
    data = _build_discover_result(db, current_user, limit, cursor)
    elapsed_ms = (time.perf_counter() - start) * 1000

    cache_set(feed_cache, cache_key, data)

    return {
        "success": True,
        "optimized": True,
        "cache_hit": False,
        "query_time_ms": round(elapsed_ms, 3),
        "cached_at": None,
        "cache_ttl_seconds": 60,
        "data": data,
    }


@router.delete("/cache/clear")
def clear_feed_cache(current_user=Depends(get_current_user)):
    """Clear the feed cache — useful for resetting between demo runs."""
    feed_cache.clear()
    return {"success": True, "message": "Feed cache cleared"}

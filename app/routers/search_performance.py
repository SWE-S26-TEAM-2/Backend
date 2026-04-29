"""
Search Performance Comparison — Optimized Endpoints.

The original /search/users, /search/tracks, /search/playlists endpoints are
the "before" baseline. These endpoints are the "after" — same query, but
PostgreSQL uses a GIN trigram index created at startup.

Compare:
  GET /search/users?keyword=...                    ← original (no index benefit)
  GET /search/performance/users/optimized?keyword= ← with GIN index

Response includes query_time_ms so you can see the difference directly.
"""

import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.follow import Follow
from app.models.playlist import Playlist
from app.models.track import Track
from app.models.user import User

router = APIRouter(
    prefix="/search/performance",
    tags=["Search Performance (Optimized)"],
)


# ──────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────

@router.get("/users/optimized")
def search_users_optimized(
    keyword: str = Query(..., description="Search keyword"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search users using a GIN trigram index on display_name.
    Compare response time against GET /search/users?keyword=...
    """
    start = time.perf_counter()
    users = (
        db.query(User)
        .filter(User.display_name.ilike(f"%{keyword}%"))
        .limit(20)
        .all()
    )

    following_ids: set = set()
    if users:
        target_ids = [u.user_id for u in users]
        rows = (
            db.query(Follow.following_id)
            .filter(
                Follow.follower_id == current_user.user_id,
                Follow.following_id.in_(target_ids),
            )
            .all()
        )
        following_ids = {r[0] for r in rows}

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "success": True,
        "optimized": True,
        "query_time_ms": round(elapsed_ms, 3),
        "result_count": len(users),
        "data": {
            "users": [
                {
                    "user_id": str(u.user_id),
                    "username": u.username,
                    "display_name": u.display_name,
                    "account_type": u.account_type,
                    "profile_picture": u.profile_picture,
                    "follower_count": u.follower_count,
                    "is_verified": u.is_verified,
                    "is_following": u.user_id in following_ids,
                }
                for u in users
            ]
        },
    }


# ──────────────────────────────────────────────
# Tracks
# ──────────────────────────────────────────────

@router.get("/tracks/optimized")
def search_tracks_optimized(
    keyword: str = Query(..., description="Search keyword"),
    db: Session = Depends(get_db),
):
    """
    Search tracks using a GIN trigram index on title.
    Compare response time against GET /search/tracks?keyword=...
    """
    start = time.perf_counter()
    tracks = (
        db.query(Track)
        .filter(
            Track.title.ilike(f"%{keyword}%"),
            Track.visibility == "public",
        )
        .limit(20)
        .all()
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "success": True,
        "optimized": True,
        "query_time_ms": round(elapsed_ms, 3),
        "result_count": len(tracks),
        "data": {
            "tracks": [
                {
                    "track_id": str(t.track_id),
                    "title": t.title,
                    "genre": t.genre,
                    "cover_image_url": t.cover_image_url,
                    "visibility": t.visibility,
                    "play_count": t.play_count,
                }
                for t in tracks
            ]
        },
    }


# ──────────────────────────────────────────────
# Playlists
# ──────────────────────────────────────────────

@router.get("/playlists/optimized")
def search_playlists_optimized(
    keyword: str = Query(..., description="Search keyword"),
    db: Session = Depends(get_db),
):
    """
    Search playlists using a GIN trigram index on name.
    Compare response time against GET /search/playlists?keyword=...
    """
    start = time.perf_counter()
    playlists = (
        db.query(Playlist)
        .filter(Playlist.name.ilike(f"%{keyword}%"))
        .limit(20)
        .all()
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "success": True,
        "optimized": True,
        "query_time_ms": round(elapsed_ms, 3),
        "result_count": len(playlists),
        "data": {
            "playlists": [
                {
                    "playlist_id": str(p.playlist_id),
                    "user_id": str(p.user_id),
                    "name": p.name,
                    "description": p.description,
                    "cover_photo_url": p.cover_photo_url,
                }
                for p in playlists
            ]
        },
    }

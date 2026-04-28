from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories.feed_repo import FeedRepository
from app.services.track_service import TrackService

_EMPTY_STATS = {
    "like_count": 0,
    "repost_count": 0,
    "comment_count": 0,
    "is_liked": False,
    "is_reposted": False,
}


class FeedService:

    @staticmethod
    def _serialize_item(track, artist, stats: dict) -> dict:
        return {
            "track_id": str(track.track_id),
            "title": track.title,
            "description": track.description,
            "genre": track.genre,
            "tags": track.tags or [],
            "release_date": track.release_date.isoformat() if track.release_date else None,
            "cover_image_url": track.cover_image_url,
            "stream_url": TrackService._get_audio_stream_url(track),
            "duration_seconds": track.duration_seconds,
            "play_count": int(track.play_count or 0),
            "like_count": stats["like_count"],
            "repost_count": stats["repost_count"],
            "comment_count": stats["comment_count"],
            "is_liked": stats["is_liked"],
            "is_reposted": stats["is_reposted"],
            "created_at": track.created_at.isoformat() if track.created_at else None,
            "artist": {
                "user_id": str(artist.user_id),
                "username": artist.username,
                "display_name": artist.display_name,
                "profile_picture": artist.profile_picture,
                "follower_count": int(artist.follower_count or 0),
            },
        }

    @staticmethod
    def get_following_feed(db: Session, user, limit: int, cursor: str | None) -> dict:
        cursor_dt: datetime | None = None
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor)
            except ValueError:
                pass

        rows = FeedRepository.get_following_feed(db, user.user_id, limit, cursor_dt)

        has_more = len(rows) > limit
        rows = rows[:limit]

        if not rows:
            return {"success": True, "data": {"items": [], "next_cursor": None, "has_more": False}}

        track_ids = [track.track_id for track, _ in rows]
        stats_map = FeedRepository.get_engagement_stats(db, track_ids, user.user_id)

        items = [
            FeedService._serialize_item(track, artist, stats_map.get(track.track_id, _EMPTY_STATS))
            for track, artist in rows
        ]

        next_cursor = None
        if has_more:
            last_track = rows[-1][0]
            if last_track.created_at:
                next_cursor = last_track.created_at.isoformat()

        return {
            "success": True,
            "data": {
                "items": items,
                "next_cursor": next_cursor,
                "has_more": has_more,
            },
        }

    @staticmethod
    def get_discover_feed(db: Session, user, limit: int, cursor: str | None) -> dict:
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
            # Backfill with trending when genre results are short
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
            return {"success": True, "data": {"items": [], "next_cursor": None, "has_more": False}}

        track_ids = [track.track_id for track, _ in rows]
        stats_map = FeedRepository.get_engagement_stats(db, track_ids, user.user_id)

        items = [
            FeedService._serialize_item(track, artist, stats_map.get(track.track_id, _EMPTY_STATS))
            for track, artist in rows
        ]

        has_more = len(items) == limit
        next_cursor = str(offset + len(items)) if has_more else None

        return {
            "success": True,
            "data": {
                "items": items,
                "next_cursor": next_cursor,
                "has_more": has_more,
            },
        }

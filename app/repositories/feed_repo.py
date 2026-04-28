from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.comment import Comment
from app.models.follow import Follow
from app.models.like import Like
from app.models.listening_history import ListeningHistory
from app.models.repost import Repost
from app.models.track import Track
from app.models.user import User


class FeedRepository:

    @staticmethod
    def get_following_ids(db: Session, user_id) -> list:
        rows = db.query(Follow.following_id).filter(Follow.follower_id == user_id).all()
        return [r[0] for r in rows]

    @staticmethod
    def get_blocked_ids(db: Session, user_id) -> set:
        blocked = db.query(Block.blocked_id).filter(Block.blocker_id == user_id).all()
        blockers = db.query(Block.blocker_id).filter(Block.blocked_id == user_id).all()
        return {r[0] for r in blocked} | {r[0] for r in blockers}

    @staticmethod
    def get_following_feed(
        db: Session,
        user_id,
        limit: int,
        cursor_dt: datetime | None,
    ) -> list:
        following_ids = FeedRepository.get_following_ids(db, user_id)
        if not following_ids:
            return []

        blocked_ids = FeedRepository.get_blocked_ids(db, user_id)

        query = (
            db.query(Track, User)
            .join(User, User.user_id == Track.user_id)
            .filter(
                Track.user_id.in_(following_ids),
                Track.visibility == "public",
            )
        )

        if blocked_ids:
            query = query.filter(~Track.user_id.in_(blocked_ids))

        if cursor_dt:
            query = query.filter(Track.created_at < cursor_dt)

        return (
            query
            .order_by(Track.created_at.desc().nullslast())
            .limit(limit + 1)
            .all()
        )

    @staticmethod
    def get_user_top_genres(db: Session, user_id, top_n: int = 5) -> list:
        history_genres = (
            db.query(Track.genre, func.count(Track.genre).label("cnt"))
            .join(ListeningHistory, ListeningHistory.track_id == Track.track_id)
            .filter(ListeningHistory.user_id == user_id, Track.genre.isnot(None))
            .group_by(Track.genre)
            .all()
        )
        liked_genres = (
            db.query(Track.genre, func.count(Track.genre).label("cnt"))
            .join(Like, Like.track_id == Track.track_id)
            .filter(Like.user_id == user_id, Track.genre.isnot(None))
            .group_by(Track.genre)
            .all()
        )
        reposted_genres = (
            db.query(Track.genre, func.count(Track.genre).label("cnt"))
            .join(Repost, Repost.track_id == Track.track_id)
            .filter(Repost.user_id == user_id, Track.genre.isnot(None))
            .group_by(Track.genre)
            .all()
        )

        scores: dict = {}
        for genre, cnt in history_genres:
            scores[genre] = scores.get(genre, 0) + cnt * 1
        for genre, cnt in liked_genres:
            scores[genre] = scores.get(genre, 0) + cnt * 2
        for genre, cnt in reposted_genres:
            scores[genre] = scores.get(genre, 0) + cnt * 3

        return [g for g, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]]

    @staticmethod
    def get_heard_track_ids(db: Session, user_id) -> set:
        played = db.query(ListeningHistory.track_id).filter(ListeningHistory.user_id == user_id).all()
        liked = db.query(Like.track_id).filter(Like.user_id == user_id).all()
        return {r[0] for r in played} | {r[0] for r in liked}

    @staticmethod
    def get_tracks_by_genres(
        db: Session,
        genres: list,
        excluded_track_ids: set,
        excluded_user_ids: set,
        limit: int,
        offset: int,
    ) -> list:
        query = (
            db.query(Track, User)
            .join(User, User.user_id == Track.user_id)
            .filter(
                Track.genre.in_(genres),
                Track.visibility == "public",
            )
        )
        if excluded_track_ids:
            query = query.filter(~Track.track_id.in_(excluded_track_ids))
        if excluded_user_ids:
            query = query.filter(~Track.user_id.in_(excluded_user_ids))

        return (
            query
            .order_by(Track.play_count.desc(), Track.created_at.desc().nullslast())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_trending_tracks(
        db: Session,
        excluded_track_ids: set,
        excluded_user_ids: set,
        limit: int,
        offset: int,
    ) -> list:
        query = (
            db.query(Track, User)
            .join(User, User.user_id == Track.user_id)
            .filter(Track.visibility == "public")
        )
        if excluded_track_ids:
            query = query.filter(~Track.track_id.in_(excluded_track_ids))
        if excluded_user_ids:
            query = query.filter(~Track.user_id.in_(excluded_user_ids))

        return (
            query
            .order_by(Track.play_count.desc(), Track.created_at.desc().nullslast())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_engagement_stats(db: Session, track_ids: list, user_id) -> dict:
        if not track_ids:
            return {}

        like_counts = dict(
            db.query(Like.track_id, func.count(Like.like_id))
            .filter(Like.track_id.in_(track_ids))
            .group_by(Like.track_id)
            .all()
        )
        repost_counts = dict(
            db.query(Repost.track_id, func.count(Repost.repost_id))
            .filter(Repost.track_id.in_(track_ids))
            .group_by(Repost.track_id)
            .all()
        )
        comment_counts = dict(
            db.query(Comment.track_id, func.count(Comment.comment_id))
            .filter(Comment.track_id.in_(track_ids))
            .group_by(Comment.track_id)
            .all()
        )
        user_liked = {
            r[0] for r in
            db.query(Like.track_id)
            .filter(Like.user_id == user_id, Like.track_id.in_(track_ids))
            .all()
        }
        user_reposted = {
            r[0] for r in
            db.query(Repost.track_id)
            .filter(Repost.user_id == user_id, Repost.track_id.in_(track_ids))
            .all()
        }

        return {
            tid: {
                "like_count": like_counts.get(tid, 0),
                "repost_count": repost_counts.get(tid, 0),
                "comment_count": comment_counts.get(tid, 0),
                "is_liked": tid in user_liked,
                "is_reposted": tid in user_reposted,
            }
            for tid in track_ids
        }

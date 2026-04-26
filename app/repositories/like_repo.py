from sqlalchemy.orm import Session  # type: ignore

from app.models.like import Like  # type: ignore
from app.models.track import Track  # type: ignore


class LikeRepository:

    @staticmethod
    def get_like(db: Session, user_id, track_id):
        return (
            db.query(Like)
            .filter(Like.user_id == user_id, Like.track_id == track_id)
            .first()
        )

    @staticmethod
    def create(db: Session, user_id, track_id) -> Like:
        like = Like(user_id=user_id, track_id=track_id)
        db.add(like)
        db.commit()
        db.refresh(like)
        return like

    @staticmethod
    def delete(db: Session, like: Like) -> None:
        db.delete(like)
        db.commit()

    @staticmethod
    def get_liked_tracks_by_user(db: Session, user_id, include_private: bool = False):
        query = (
            db.query(Track)
            .join(Like, Like.track_id == Track.track_id)
            .filter(Like.user_id == user_id)
            .order_by(Like.created_at.desc())
        )

        if not include_private:
            query = query.filter(Track.visibility == "public")

        return query.all()

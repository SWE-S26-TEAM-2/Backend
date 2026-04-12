from sqlalchemy.orm import Session  # type: ignore

from app.models.like import Like  # type: ignore


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

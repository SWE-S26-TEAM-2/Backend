from sqlalchemy.orm import Session  # type: ignore

from app.models.repost import Repost  # type: ignore


class RepostRepository:

    @staticmethod
    def get_repost(db: Session, user_id, track_id):
        return (
            db.query(Repost)
            .filter(Repost.user_id == user_id, Repost.track_id == track_id)
            .first()
        )

    @staticmethod
    def create(db: Session, user_id, track_id) -> Repost:
        repost = Repost(user_id=user_id, track_id=track_id)
        db.add(repost)
        db.commit()
        db.refresh(repost)
        return repost

    @staticmethod
    def delete(db: Session, repost: Repost) -> None:
        db.delete(repost)
        db.commit()

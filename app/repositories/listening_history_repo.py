from sqlalchemy.orm import Session  # type: ignore

from app.models.listening_history import ListeningHistory
from app.models.track import Track


class ListeningHistoryRepository:
    @staticmethod
    def create(db: Session, history: ListeningHistory):
        db.add(history)
        return history

    @staticmethod
    def get_by_user_id(db: Session, user_id, limit: int = 20):
        return (
            db.query(ListeningHistory, Track)
            .join(Track, ListeningHistory.track_id == Track.track_id)
            .filter(ListeningHistory.user_id == user_id)
            .order_by(ListeningHistory.played_at.desc())
            .limit(limit)
            .all()
        )

from sqlalchemy.orm import Session  # type: ignore

from app.models.track import Track


class TrackRepository:

    @staticmethod
    def create(db: Session, track: Track):
        db.add(track)
        db.commit()
        db.refresh(track)
        return track

    @staticmethod
    def get_by_id(db: Session, track_id):
        return db.query(Track).filter(
            Track.track_id == track_id
        ).first()

    @staticmethod
    def search_by_title(db: Session, keyword: str):
        return db.query(Track).filter(
            Track.title.ilike(f"%{keyword}%")
        ).all()

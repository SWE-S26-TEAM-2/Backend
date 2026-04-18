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
        return db.query(Track).filter(Track.track_id == track_id).first()

    @staticmethod
    def get_by_user_id_and_file_hash(db: Session, user_id, file_hash: str):
        return (
            db.query(Track)
            .filter(
                Track.user_id == user_id,
                Track.file_hash == file_hash,
            )
            .first()
        )

    @staticmethod
    def search_by_title(db: Session, keyword: str):
        return (
            db.query(Track)
            .filter(
                Track.title.ilike(f"%{keyword}%"),
                Track.visibility == "public",
            )
            .all()
        )

from sqlalchemy.orm import Session  # type: ignore

from app.models.album import Album
from app.models.album_like import AlbumLike
from app.models.album_track import AlbumTrack


class AlbumRepository:

    @staticmethod
    def create(db: Session, album: Album) -> Album:
        db.add(album)
        db.commit()
        db.refresh(album)
        return album

    @staticmethod
    def get_by_id(db: Session, album_id) -> Album | None:
        return db.query(Album).filter(Album.album_id == album_id).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id, include_private: bool = False):
        query = db.query(Album).filter(Album.user_id == user_id)
        if not include_private:
            query = query.filter(Album.visibility == "public")
        return query.order_by(Album.created_at.desc()).all()

    @staticmethod
    def count_by_user_id(db: Session, user_id) -> int:
        return db.query(Album).filter(Album.user_id == user_id).count()

    @staticmethod
    def update(db: Session, album: Album, fields: dict) -> Album:
        for key, value in fields.items():
            setattr(album, key, value)
        db.commit()
        db.refresh(album)
        return album

    @staticmethod
    def delete(db: Session, album: Album) -> None:
        db.delete(album)
        db.commit()

    # ── Album tracks ──────────────────────────────────────

    @staticmethod
    def get_max_position(db: Session, album_id) -> int:
        result = (
            db.query(AlbumTrack)
            .filter(AlbumTrack.album_id == album_id)
            .order_by(AlbumTrack.position.desc())
            .first()
        )
        return result.position if result else 0

    @staticmethod
    def add_track(db: Session, album_id, track_id, position: int) -> AlbumTrack:
        album_track = AlbumTrack(
            album_id=album_id,
            track_id=track_id,
            position=position,
        )
        db.add(album_track)
        db.commit()
        db.refresh(album_track)
        return album_track

    @staticmethod
    def get_album_track(db: Session, album_id, track_id) -> AlbumTrack | None:
        return (
            db.query(AlbumTrack)
            .filter(
                AlbumTrack.album_id == album_id,
                AlbumTrack.track_id == track_id,
            )
            .first()
        )

    @staticmethod
    def get_track_album(db: Session, track_id) -> AlbumTrack | None:
        """Return the AlbumTrack row for a track (a track can only be in one album)."""
        return (
            db.query(AlbumTrack)
            .filter(AlbumTrack.track_id == track_id)
            .first()
        )

    @staticmethod
    def get_album_tracks(db: Session, album_id):
        return (
            db.query(AlbumTrack)
            .filter(AlbumTrack.album_id == album_id)
            .order_by(AlbumTrack.position.asc())
            .all()
        )

    @staticmethod
    def get_album_tracks_by_track(db: Session, track_id):
        return (
            db.query(AlbumTrack)
            .filter(AlbumTrack.track_id == track_id)
            .all()
        )

    @staticmethod
    def remove_track(db: Session, album_track: AlbumTrack) -> None:
        db.delete(album_track)
        db.commit()

    @staticmethod
    def reorder_tracks(db: Session, album_id, ordered_track_ids: list) -> None:
        for position, track_id in enumerate(ordered_track_ids, start=1):
            db.query(AlbumTrack).filter(
                AlbumTrack.album_id == album_id,
                AlbumTrack.track_id == track_id,
            ).update({"position": position})
        db.commit()

    # ── Album likes ───────────────────────────────────────

    @staticmethod
    def get_album_like(db: Session, user_id, album_id) -> AlbumLike | None:
        return (
            db.query(AlbumLike)
            .filter(
                AlbumLike.user_id == user_id,
                AlbumLike.album_id == album_id,
            )
            .first()
        )

    @staticmethod
    def create_album_like(db: Session, user_id, album_id) -> AlbumLike:
        album_like = AlbumLike(
            user_id=user_id,
            album_id=album_id,
        )
        db.add(album_like)
        db.commit()
        db.refresh(album_like)
        return album_like

    @staticmethod
    def delete_album_like(db: Session, album_like: AlbumLike) -> None:
        db.delete(album_like)
        db.commit()

    @staticmethod
    def get_liked_albums(db: Session, user_id):
        return (
            db.query(Album)
            .join(AlbumLike, Album.album_id == AlbumLike.album_id)
            .filter(AlbumLike.user_id == user_id)
            .order_by(AlbumLike.created_at.desc())
            .all()
        )

    @staticmethod
    def search_by_title(db: Session, keyword: str):
        return (
            db.query(Album)
            .filter(
                Album.title.ilike(f"%{keyword}%"),
                Album.visibility == "public",
            )
            .all()
        )

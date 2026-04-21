from sqlalchemy.orm import Session  # type: ignore

from app.models.playlist import Playlist
from app.models.playlist_like import PlaylistLike
from app.models.playlist_track import PlaylistTrack


class PlaylistRepository:

    @staticmethod
    def create(db: Session, playlist: Playlist):
        db.add(playlist)
        db.commit()
        db.refresh(playlist)
        return playlist

    @staticmethod
    def get_by_id(db: Session, playlist_id):
        return db.query(Playlist).filter(Playlist.playlist_id == playlist_id).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id):
        return db.query(Playlist).filter(Playlist.user_id == user_id).all()

    @staticmethod
    def update(db: Session, playlist: Playlist, fields: dict):
        for key, value in fields.items():
            setattr(playlist, key, value)
        db.commit()
        db.refresh(playlist)
        return playlist

    @staticmethod
    def delete(db: Session, playlist: Playlist):
        db.delete(playlist)
        db.commit()

    @staticmethod
    def add_track(db: Session, playlist_id, track_id):
        playlist_track = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=track_id,
        )
        db.add(playlist_track)
        db.commit()
        db.refresh(playlist_track)
        return playlist_track

    @staticmethod
    def get_playlist_track(db: Session, playlist_id, track_id):
        return (
            db.query(PlaylistTrack)
            .filter(
                PlaylistTrack.playlist_id == playlist_id,
                PlaylistTrack.track_id == track_id,
            )
            .first()
        )

    @staticmethod
    def remove_track(db: Session, playlist_track: PlaylistTrack):
        db.delete(playlist_track)
        db.commit()

    @staticmethod
    def get_playlist_tracks(db: Session, playlist_id):
        return (
            db.query(PlaylistTrack)
            .filter(PlaylistTrack.playlist_id == playlist_id)
            .all()
        )

    @staticmethod
    def get_playlist_tracks_by_track(db, track_id):
        return db.query(PlaylistTrack).filter(PlaylistTrack.track_id == track_id).all()

    @staticmethod
    def get_playlist_like(db: Session, user_id, playlist_id):
        return (
            db.query(PlaylistLike)
            .filter(
                PlaylistLike.user_id == user_id,
                PlaylistLike.playlist_id == playlist_id,
            )
            .first()
        )

    @staticmethod
    def create_playlist_like(db: Session, user_id, playlist_id):
        playlist_like = PlaylistLike(
            user_id=user_id,
            playlist_id=playlist_id,
        )
        db.add(playlist_like)
        db.commit()
        db.refresh(playlist_like)
        return playlist_like

    @staticmethod
    def delete_playlist_like(db: Session, playlist_like: PlaylistLike):
        db.delete(playlist_like)
        db.commit()

    @staticmethod
    def get_liked_playlists(db: Session, user_id):
        return (
            db.query(Playlist)
            .join(
                PlaylistLike,
                Playlist.playlist_id == PlaylistLike.playlist_id,
            )
            .filter(PlaylistLike.user_id == user_id)
            .all()
        )

    @staticmethod
    def search_by_name(db: Session, keyword: str):
        return db.query(Playlist).filter(Playlist.name.ilike(f"%{keyword}%")).all()

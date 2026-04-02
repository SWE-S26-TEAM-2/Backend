from sqlalchemy.orm import Session  # type: ignore
from app.models.playlist import Playlist
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
        return db.query(Playlist).filter(
            Playlist.playlist_id == playlist_id
        ).first()

    @staticmethod
    def delete(db: Session, playlist):
        db.delete(playlist)
        db.commit()

    @staticmethod
    def add_track(db: Session, playlist_id, track_id):
        pt = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=track_id
        )
        db.add(pt)
        db.commit()

    @staticmethod
    def remove_track(db: Session, playlist_id, track_id):
        db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.track_id == track_id
        ).delete()
        db.commit()
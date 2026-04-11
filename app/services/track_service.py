from fastapi import HTTPException, status  # type: ignore

from app.models.track import Track
from app.repositories.track_repo import TrackRepository
from app.repositories.playlist_repo import PlaylistRepository


class TrackService:

    @staticmethod
    def create_track(db, user, data):
        track = Track(
            user_id=user.user_id,
            title=data.title,
            description=data.description,
            file_url=data.file_url,
        )

        TrackRepository.create(db, track)

        return {
            "success": True,
            "message": "Track created successfully.",
            "data": {
                "track_id": str(track.track_id),
                "title": track.title,
            },
        }

    @staticmethod
    def delete_track(db, user, track_id):
        track = TrackRepository.get_by_id(db, track_id)

        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found",
            )

        if str(track.user_id) != str(user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own tracks",
            )

        # optional: remove from playlists
        playlist_tracks = PlaylistRepository.get_playlist_tracks_by_track(
            db, track_id
        )
        for pt in playlist_tracks:
            db.delete(pt)

        db.delete(track)
        db.commit()

        return {
            "success": True,
            "message": "Track deleted successfully",
        }

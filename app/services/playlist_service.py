from fastapi import HTTPException, status  # type: ignore

from app.models.playlist import Playlist
from app.repositories.playlist_repo import PlaylistRepository
from app.repositories.track_repo import TrackRepository


class PlaylistService:

    @staticmethod
    def create_playlist(db, user, data):
        playlist = Playlist(
            user_id=user.user_id,
            name=data.name,
            description=data.description,
        )
        PlaylistRepository.create(db, playlist)

        return {
            "success": True,
            "message": "Playlist created successfully.",
            "data": {
                "playlist_id": str(playlist.playlist_id),
                "name": playlist.name,
                "description": playlist.description,
            },
        }

    @staticmethod
    def get_playlist(db, playlist_id):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        return {
            "success": True,
            "data": {
                "playlist_id": str(playlist.playlist_id),
                "user_id": str(playlist.user_id),
                "name": playlist.name,
                "description": playlist.description,
                "tracks": []
            },
        }

    @staticmethod
    def update_playlist(db, user, playlist_id, data):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        if str(playlist.user_id) != str(user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own playlists",
            )

        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        updated_playlist = PlaylistRepository.update(
            db, playlist, update_data
        )

        return {
            "success": True,
            "message": "Playlist updated successfully.",
            "data": {
                "playlist_id": str(updated_playlist.playlist_id),
                "name": updated_playlist.name,
                "description": updated_playlist.description,
            },
        }

    @staticmethod
    def delete_playlist(db, user, playlist_id):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        if str(playlist.user_id) != str(user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own playlists",
            )

        PlaylistRepository.delete(db, playlist)

        return {
            "success": True,
            "message": "Playlist deleted successfully.",
        }

    @staticmethod
    def add_track_to_playlist(db, user, playlist_id, data):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        if str(playlist.user_id) != str(user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own playlists",
            )

        track = TrackRepository.get_by_id(db, data.track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found",
            )

        existing = PlaylistRepository.get_playlist_track(
            db, playlist_id, data.track_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Track already exists in playlist",
            )

        PlaylistRepository.add_track(db, playlist_id, data.track_id)

        return {
            "success": True,
            "message": "Track added to playlist successfully.",
        }

    @staticmethod
    def remove_track_from_playlist(db, user, playlist_id, track_id):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        if str(playlist.user_id) != str(user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own playlists",
            )

        playlist_track = PlaylistRepository.get_playlist_track(
            db, playlist_id, track_id
        )
        if not playlist_track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found in playlist",
            )

        PlaylistRepository.remove_track(db, playlist_track)

        return {
            "success": True,
            "message": "Track removed from playlist successfully.",
        }

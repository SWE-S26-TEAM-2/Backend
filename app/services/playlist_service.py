from fastapi import HTTPException, status  # type: ignore
from fastapi import UploadFile  # type: ignore
import os

from app.models.playlist import Playlist
from app.repositories.notification_repo import NotificationRepository
from app.repositories.playlist_repo import PlaylistRepository
from app.repositories.track_repo import TrackRepository

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
PUBLIC_UPLOAD_BASE_URL = os.environ.get("PUBLIC_UPLOAD_BASE_URL", "/api/uploads")
COVER_PHOTO_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


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
                "cover_photo_url": playlist.cover_photo_url,
            },
        }

    @staticmethod
    def get_liked_playlists(db, user):
        playlists = PlaylistRepository.get_liked_playlists(db, user.user_id)

        return {
            "success": True,
            "data": [
                {
                    "playlist_id": str(playlist.playlist_id),
                    "user_id": str(playlist.user_id),
                    "name": playlist.name,
                    "description": playlist.description,
                    "cover_photo_url": playlist.cover_photo_url,
                }
                for playlist in playlists
            ],
        }

    @staticmethod
    def get_playlist(db, playlist_id):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        playlist_tracks = PlaylistRepository.get_playlist_tracks(db, playlist_id)
        tracks = []

        for playlist_track in playlist_tracks:
            track = TrackRepository.get_by_id(db, playlist_track.track_id)
            if track:
                tracks.append(
                    {
                        "track_id": str(track.track_id),
                        "user_id": str(track.user_id),
                        "title": track.title,
                        "description": track.description,
                        "genre": track.genre,
                        "tags": track.tags,
                        "release_date": track.release_date,
                        "file_url": track.file_url,
                        "visibility": track.visibility,
                        "play_count": track.play_count,
                        "duration_seconds": track.duration_seconds,
                    }
                )

        return {
            "success": True,
            "data": {
                "playlist_id": str(playlist.playlist_id),
                "user_id": str(playlist.user_id),
                "name": playlist.name,
                "description": playlist.description,
                "cover_photo_url": playlist.cover_photo_url,
                "tracks": tracks,
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

        updated_playlist = PlaylistRepository.update(db, playlist, update_data)

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
    def like_playlist(db, user, playlist_id):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        existing = PlaylistRepository.get_playlist_like(db, user.user_id, playlist_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already liked this playlist",
            )

        playlist_like = PlaylistRepository.create_playlist_like(
            db, user.user_id, playlist_id
        )

        # Notify playlist owner (skip if liking own playlist)
        if str(playlist.user_id) != str(user.user_id):
            NotificationRepository.create(
                db,
                user_id=playlist.user_id,
                actor_id=user.user_id,
                notification_type="like",
                message=f'{user.display_name} liked your playlist "{playlist.name}".',
                target_id=playlist_id,
            )

        return {
            "success": True,
            "message": "Playlist liked successfully.",
            "data": {
                "playlist_like_id": str(playlist_like.playlist_like_id),
                "playlist_id": str(playlist_id),
            },
        }

    @staticmethod
    def unlike_playlist(db, user, playlist_id):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        existing = PlaylistRepository.get_playlist_like(db, user.user_id, playlist_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have not liked this playlist",
            )

        PlaylistRepository.delete_playlist_like(db, existing)

        return {
            "success": True,
            "message": "Playlist unliked successfully.",
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

        existing = PlaylistRepository.get_playlist_track(db, playlist_id, data.track_id)
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

    @staticmethod
    def upload_cover_photo(db, user, playlist_id, file: UploadFile):
        playlist = PlaylistRepository.get_by_id(db, playlist_id)
        if not playlist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playlist not found",
            )

        if str(playlist.user_id) != str(user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload cover photos for your own playlists",
            )

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded",
            )

        if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed (JPEG, PNG, GIF, WebP)",
            )

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > COVER_PHOTO_MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must not exceed 5 MB",
            )

        file_extension = os.path.splitext(file.filename)[1] or ".jpg"
        unique_filename = f"playlist_{playlist_id}{file_extension}"

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        cover_photo_url = f"{PUBLIC_UPLOAD_BASE_URL.rstrip('/')}/{unique_filename}"

        PlaylistRepository.update(db, playlist, {"cover_photo_url": cover_photo_url})

        return {
            "success": True,
            "message": "Cover photo uploaded successfully.",
            "data": {
                "playlist_id": str(playlist.playlist_id),
                "cover_photo_url": cover_photo_url,
            },
        }

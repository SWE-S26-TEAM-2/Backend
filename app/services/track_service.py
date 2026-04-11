from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import os
from uuid import UUID, uuid4  # type: ignore

from app.models.track import Track
from app.repositories.track_repo import TrackRepository
from app.repositories.playlist_repo import PlaylistRepository


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")


class TrackService:

    @staticmethod
    def create_track(
        db: Session,
        user,
        title: str,
        description: str,
        file: UploadFile,
    ):
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded",
            )

        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only audio files are allowed",
            )

        file_extension = os.path.splitext(file.filename)[1] or ".mp3"
        unique_filename = f"{uuid4()}{file_extension}"

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        file_url = f"http://127.0.0.1:8000/api/uploads/{unique_filename}"

        track = Track(
            user_id=user.user_id,
            title=title,
            description=description,
            file_url=file_url,
        )

        TrackRepository.create(db, track)

        return {
            "success": True,
            "message": "Track uploaded successfully.",
            "data": {
                "track_id": str(track.track_id),
                "title": track.title,
                "file_url": track.file_url,
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

    @staticmethod
    def get_track_by_id(db: Session, track_id: UUID):
        track = TrackRepository.get_by_id(db, track_id)

        if not track:
            return None

        return track

    @staticmethod
    def update_track(db: Session, track_id: UUID, track_data, user_id: UUID):
        track = TrackRepository.get_by_id(db, track_id)

        if not track:
            return None

        if str(track.user_id) != str(user_id):
            return "forbidden"

        if track_data.title is not None:
            track.title = track_data.title

        if track_data.description is not None:
            track.description = track_data.description

        if track_data.file_url is not None:
            track.file_url = track_data.file_url

        if track_data.visibility is not None:
            track.visibility = track_data.visibility

        db.commit()
        db.refresh(track)

        return track

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import hashlib
import os
import mimetypes
from datetime import date
from uuid import UUID, uuid4  # type: ignore
from pydub import AudioSegment  # type: ignore

from app.models.track import Track
from app.models.listening_history import ListeningHistory
from app.repositories.listening_history_repo import ListeningHistoryRepository
from app.repositories.track_repo import TrackRepository
from app.repositories.playlist_repo import PlaylistRepository


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
TRACK_MAX_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_VISIBILITIES = {"public", "private"}


class TrackService:
    @staticmethod
    def _calculate_file_hash(file) -> str:
        file.seek(0)
        digest = hashlib.sha256()

        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

        file.seek(0)
        return digest.hexdigest()

    @staticmethod
    def _get_content_type(track):
        content_type, _ = mimetypes.guess_type(track.file_url or "")
        return content_type or "audio/mpeg"

    @staticmethod
    def _get_track_or_404(db: Session, track_id: UUID):
        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found",
            )
        return track

    @staticmethod
    def _ensure_track_access(track, user=None):
        if track.visibility == "private" and (
            user is None or str(track.user_id) != str(user.user_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Track is private",
            )

    @staticmethod
    def _validate_visibility(visibility: str):
        if visibility not in ALLOWED_VISIBILITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Visibility must be 'public' or 'private'",
            )

    @staticmethod
    def _parse_tags(tags: str | None) -> list[str] | None:
        if tags is None:
            return None

        parsed_tags = [
            tag.strip()
            for tag in tags.split(",")
            if tag.strip()
        ]
        return parsed_tags or None

    @staticmethod
    def _serialize_track(track):
        return {
            "track_id": str(track.track_id),
            "title": track.title,
            "description": track.description,
            "genre": track.genre,
            "tags": track.tags or [],
            "release_date": (
                track.release_date.isoformat() if track.release_date else None
            ),
            "file_url": track.file_url,
            "user_id": str(track.user_id),
            "visibility": track.visibility,
            "processing_status": track.processing_status,
            "play_count": int(track.play_count or 0),
            "duration_seconds": track.duration_seconds,
        }

    @staticmethod
    def _get_waveform_data(db: Session, track, user=None):
        TrackService._ensure_track_access(track, user)

        if track.waveform_peaks:
            return {
                "track_id": str(track.track_id),
                "duration_seconds": track.duration_seconds,
                "sample_count": len(track.waveform_peaks),
                "peaks": track.waveform_peaks,
            }

        filename = track.file_url.split("/")[-1]
        file_path = os.path.join(UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found",
            )

        audio = AudioSegment.from_file(file_path)
        audio = audio.set_channels(1)

        sample_count = 200
        duration_ms = len(audio)
        bucket_size = max(1, duration_ms // sample_count)

        peaks = []

        for i in range(sample_count):
            start = i * bucket_size
            end = min(start + bucket_size, duration_ms)
            chunk = audio[start:end]

            if len(chunk) == 0:
                peak = 0
            else:
                peak = chunk.max / audio.max_possible_amplitude

            peaks.append(round(peak, 4))

        track.duration_seconds = duration_ms // 1000
        track.waveform_peaks = peaks

        db.commit()
        db.refresh(track)

        return {
            "track_id": str(track.track_id),
            "duration_seconds": track.duration_seconds,
            "sample_count": len(peaks),
            "peaks": peaks,
        }

    @staticmethod
    def create_track(
        db: Session,
        user,
        title: str,
        description: str,
        file: UploadFile,
        genre: str | None = None,
        tags: str | None = None,
        release_date: date | None = None,
        visibility: str = "public",
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

        TrackService._validate_visibility(visibility)

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > TRACK_MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must not exceed 100 MB",
            )

        file_hash = TrackService._calculate_file_hash(file.file)
        existing_track = TrackRepository.get_by_user_id_and_file_hash(
            db,
            user.user_id,
            file_hash,
        )

        if existing_track:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already uploaded this track",
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
            genre=genre,
            tags=TrackService._parse_tags(tags),
            release_date=release_date,
            file_url=file_url,
            file_hash=file_hash,
            visibility=visibility,
            processing_status="finished",
        )

        TrackRepository.create(db, track)

        return {
            "success": True,
            "message": "Track uploaded successfully.",
            "data": {
                "track_id": str(track.track_id),
                "title": track.title,
                "genre": track.genre,
                "tags": track.tags or [],
                "release_date": (
                    track.release_date.isoformat() if track.release_date else None
                ),
                "file_url": track.file_url,
                "visibility": track.visibility,
                "processing_status": track.processing_status,
            },
        }

    @staticmethod
    def get_track_details(db: Session, track_id: UUID, user=None):
        track = TrackService._get_track_or_404(db, track_id)
        TrackService._ensure_track_access(track, user)
        return {"success": True, "data": TrackService._serialize_track(track)}

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
        playlist_tracks = PlaylistRepository.get_playlist_tracks_by_track(db, track_id)
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

        update_data = track_data.model_dump(exclude_unset=True)
        if "visibility" in update_data:
            TrackService._validate_visibility(update_data["visibility"])

        if track_data.title is not None:
            track.title = track_data.title

        if track_data.description is not None:
            track.description = track_data.description

        if track_data.genre is not None:
            track.genre = track_data.genre

        if track_data.tags is not None:
            track.tags = track_data.tags

        if track_data.release_date is not None:
            track.release_date = track_data.release_date

        if track_data.file_url is not None:
            track.file_url = track_data.file_url
            track.waveform_peaks = None
            track.duration_seconds = None

        if track_data.visibility is not None:
            track.visibility = track_data.visibility

        db.commit()
        db.refresh(track)

        return track

    @staticmethod
    def get_waveform(db: Session, track_id: UUID, user=None):
        track = TrackService._get_track_or_404(db, track_id)
        return {
            "success": True,
            "data": TrackService._get_waveform_data(db, track, user),
        }

    @staticmethod
    def get_stream(db: Session, track_id: UUID, user=None):
        track = TrackService._get_track_or_404(db, track_id)
        TrackService._ensure_track_access(track, user)

        return {
            "success": True,
            "data": {
                "track_id": str(track.track_id),
                "stream_url": track.file_url,
                "expires_in": None,
                "content_type": TrackService._get_content_type(track),
                "play_count": int(track.play_count or 0),
                "processing_status": track.processing_status,
            },
        }

    @staticmethod
    def record_play(
        db: Session,
        track_id: UUID,
        user=None,
        duration_listened_seconds: int | None = None,
    ):
        track = TrackService._get_track_or_404(db, track_id)
        TrackService._ensure_track_access(track, user)
        track.play_count = int(track.play_count or 0) + 1

        if user is not None:
            history = ListeningHistory(
                user_id=user.user_id,
                track_id=track.track_id,
                duration_listened_seconds=duration_listened_seconds,
            )
            ListeningHistoryRepository.create(db, history)

        db.commit()
        db.refresh(track)

        return {
            "success": True,
            "message": "Play recorded successfully.",
            "data": {
                "track_id": str(track.track_id),
                "play_count": int(track.play_count or 0),
            },
        }

    @staticmethod
    def get_listening_history(db: Session, user, limit: int = 20):
        rows = ListeningHistoryRepository.get_by_user_id(
            db,
            user.user_id,
            limit,
        )

        return {
            "success": True,
            "data": {
                "items": [
                    TrackService._serialize_history_item(history, track)
                    for history, track in rows
                ]
            },
        }

    @staticmethod
    def _serialize_history_item(history, track):
        return {
            "history_id": str(history.history_id),
            "played_at": (
                history.played_at.isoformat() if history.played_at else None
            ),
            "duration_listened_seconds": history.duration_listened_seconds,
            "track": {
                "track_id": str(track.track_id),
                "title": track.title,
                "description": track.description,
                "file_url": track.file_url,
                "duration_seconds": track.duration_seconds,
                "play_count": int(track.play_count or 0),
            },
        }

    @staticmethod
    def get_playback(db: Session, track_id: UUID, user=None):
        track = TrackService._get_track_or_404(db, track_id)
        TrackService._ensure_track_access(track, user)
        waveform = TrackService._get_waveform_data(db, track, user)

        return {
            "success": True,
            "data": {
                "track_id": str(track.track_id),
                "title": track.title,
                "description": track.description,
                "stream_url": track.file_url,
                "expires_in": None,
                "content_type": TrackService._get_content_type(track),
                "play_count": int(track.play_count or 0),
                "processing_status": track.processing_status,
                "genre": track.genre,
                "tags": track.tags or [],
                "release_date": (
                    track.release_date.isoformat()
                    if track.release_date else None
                ),
                "duration_seconds": waveform["duration_seconds"],
                "waveform": {
                    "sample_count": waveform["sample_count"],
                    "peaks": waveform["peaks"],
                },
            },
        }

from fastapi import HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import hashlib
import os
import mimetypes
from datetime import date
from urllib.parse import unquote, urlparse
from uuid import UUID, uuid4  # type: ignore
from pydub import AudioSegment  # type: ignore

from app.models.track import Track
from app.models.listening_history import ListeningHistory
from app.repositories.follow_repo import FollowRepository
from app.repositories.like_repo import LikeRepository
from app.repositories.listening_history_repo import ListeningHistoryRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.track_repo import TrackRepository
from app.repositories.playlist_repo import PlaylistRepository
from app.repositories.user_repo import UserRepository

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
PUBLIC_UPLOAD_BASE_URL = os.environ.get("PUBLIC_UPLOAD_BASE_URL", "/api/uploads")
TRACK_MAX_SIZE = 100 * 1024 * 1024  # 100 MB
COVER_IMAGE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VISIBILITIES = {"public", "private"}


class TrackService:
    STREAM_CHUNK_SIZE = 1024 * 1024

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
    def _get_upload_filename(file_url: str | None) -> str:
        if not file_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found",
            )

        parsed_path = urlparse(file_url).path or file_url
        filename = os.path.basename(unquote(parsed_path.rstrip("/")))

        if not filename or filename in {".", ".."}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found",
            )

        return filename

    @staticmethod
    def _get_audio_file_path(track) -> str:
        filename = TrackService._get_upload_filename(track.file_url)
        return os.path.join(UPLOAD_DIR, filename)

    @staticmethod
    def _get_upload_url(filename: str) -> str:
        return f"{PUBLIC_UPLOAD_BASE_URL.rstrip('/')}/{filename}"

    @staticmethod
    def _ensure_audio_file_exists(file_url: str | None):
        filename = TrackService._get_upload_filename(file_url)
        file_path = os.path.join(UPLOAD_DIR, filename)

        if not os.path.isfile(file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file does not exist in uploads",
            )

    @staticmethod
    def _get_audio_stream_url(track):
        return f"/api/tracks/{track.track_id}/audio"

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

        parsed_tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
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
            "cover_image_url": track.cover_image_url,
            "stream_url": TrackService._get_audio_stream_url(track),
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

        file_path = TrackService._get_audio_file_path(track)

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
        cover_image: UploadFile | None = None,
    ):
        if not user.is_premium and user.track_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Free plan limit reached. "
                    "Upgrade to Premium for unlimited uploads."
                ),
            )

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

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Validate cover image if provided
        cover_image_url = None
        if cover_image and cover_image.filename:
            if (
                not cover_image.content_type
                or cover_image.content_type not in ALLOWED_IMAGE_TYPES
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cover image must be JPEG, PNG, WebP, or GIF",
                )

            cover_image.file.seek(0, os.SEEK_END)
            image_size = cover_image.file.tell()
            cover_image.file.seek(0)

            if image_size > COVER_IMAGE_MAX_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cover image must not exceed 10 MB",
                )

            img_extension = os.path.splitext(cover_image.filename)[1] or ".jpg"
            unique_img_name = f"{uuid4()}{img_extension}"
            img_path = os.path.join(UPLOAD_DIR, unique_img_name)

            with open(img_path, "wb") as img_buffer:
                img_buffer.write(cover_image.file.read())

            cover_image_url = TrackService._get_upload_url(unique_img_name)

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

        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        file_url = TrackService._get_upload_url(unique_filename)

        track = Track(
            user_id=user.user_id,
            title=title,
            description=description,
            genre=genre,
            tags=TrackService._parse_tags(tags),
            release_date=release_date,
            file_url=file_url,
            file_hash=file_hash,
            cover_image_url=cover_image_url,
            visibility=visibility,
            processing_status="finished",
        )

        TrackRepository.create(db, track)

        user.track_count = (user.track_count or 0) + 1
        db.commit()

        # Notify all followers about the new track (only if public)
        if visibility == "public":
            followers = FollowRepository.get_followers_of(db, user.user_id)
            for follow in followers:
                NotificationRepository.create(
                    db,
                    user_id=follow.follower_id,
                    actor_id=user.user_id,
                    notification_type="new_track",
                    message=f'{user.display_name} posted a new track: "{title}".',
                    target_id=track.track_id,
                )

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
                "cover_image_url": track.cover_image_url,
                "stream_url": TrackService._get_audio_stream_url(track),
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
    def get_tracks_by_user(db: Session, user_id: UUID, current_user=None):
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        include_private = current_user is not None and str(current_user.user_id) == str(
            user_id
        )
        tracks = TrackRepository.get_by_user_id(
            db,
            user_id,
            include_private=include_private,
        )

        return {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "tracks": [TrackService._serialize_track(track) for track in tracks],
            },
        }

    @staticmethod
    def get_liked_tracks_by_user(db: Session, user_id: UUID, current_user=None):
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        include_private = current_user is not None and str(current_user.user_id) == str(
            user_id
        )
        tracks = LikeRepository.get_liked_tracks_by_user(
            db,
            user_id,
            include_private=include_private,
        )

        return {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "tracks": [TrackService._serialize_track(track) for track in tracks],
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
        playlist_tracks = PlaylistRepository.get_playlist_tracks_by_track(db, track_id)
        for pt in playlist_tracks:
            db.delete(pt)

        user.track_count = max(0, (user.track_count or 0) - 1)
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
            TrackService._ensure_audio_file_exists(track_data.file_url)
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
                "stream_url": TrackService._get_audio_stream_url(track),
                "expires_in": None,
                "content_type": TrackService._get_content_type(track),
                "play_count": int(track.play_count or 0),
                "processing_status": track.processing_status,
            },
        }

    @staticmethod
    def stream_audio(db: Session, track_id: UUID, request: Request, user=None):
        track = TrackService._get_track_or_404(db, track_id)
        TrackService._ensure_track_access(track, user)

        file_path = TrackService._get_audio_file_path(track)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file not found",
            )

        file_size = os.path.getsize(file_path)
        content_type = TrackService._get_content_type(track)
        range_header = request.headers.get("range")

        def iter_file(start: int, end: int):
            with open(file_path, "rb") as audio_file:
                audio_file.seek(start)
                bytes_remaining = end - start + 1

                while bytes_remaining > 0:
                    chunk = audio_file.read(
                        min(TrackService.STREAM_CHUNK_SIZE, bytes_remaining)
                    )
                    if not chunk:
                        break

                    bytes_remaining -= len(chunk)
                    yield chunk

        if not range_header:
            return StreamingResponse(
                iter_file(0, file_size - 1),
                media_type=content_type,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(file_size),
                },
            )

        try:
            range_value = range_header.strip().lower()
            if not range_value.startswith("bytes="):
                raise ValueError

            start_text, end_text = range_value.replace("bytes=", "", 1).split("-", 1)

            if start_text == "":
                suffix_length = int(end_text)
                if suffix_length <= 0:
                    raise ValueError
                start = max(file_size - suffix_length, 0)
                end = file_size - 1
            else:
                start = int(start_text)
                end = int(end_text) if end_text else file_size - 1

            if start < 0 or end >= file_size or start > end:
                raise ValueError
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
                detail="Requested range is not satisfiable",
                headers={"Content-Range": f"bytes */{file_size}"},
            )

        content_length = end - start + 1
        return StreamingResponse(
            iter_file(start, end),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            media_type=content_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(content_length),
            },
        )

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
            "played_at": (history.played_at.isoformat() if history.played_at else None),
            "duration_listened_seconds": history.duration_listened_seconds,
            "track": {
                "track_id": str(track.track_id),
                "title": track.title,
                "description": track.description,
                "cover_image_url": track.cover_image_url,
                "stream_url": TrackService._get_audio_stream_url(track),
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
                "stream_url": TrackService._get_audio_stream_url(track),
                "cover_image_url": track.cover_image_url,
                "expires_in": None,
                "content_type": TrackService._get_content_type(track),
                "play_count": int(track.play_count or 0),
                "processing_status": track.processing_status,
                "genre": track.genre,
                "tags": track.tags or [],
                "release_date": (
                    track.release_date.isoformat() if track.release_date else None
                ),
                "duration_seconds": waveform["duration_seconds"],
                "waveform": {
                    "sample_count": waveform["sample_count"],
                    "peaks": waveform["peaks"],
                },
            },
        }

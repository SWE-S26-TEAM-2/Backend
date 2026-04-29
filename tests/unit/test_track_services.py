from io import BytesIO
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
import os
import pytest
from fastapi import HTTPException

from app.services.track_service import TrackService


class FakeDB:
    def __init__(self):
        self.added = []
        self.deleted = []
        self.committed = False
        self.refreshed = None

    def add(self, obj):
        self.added.append(obj)

    def delete(self, obj):
        self.deleted.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed = obj


class FakeUser:
    def __init__(self, user_id, is_premium=True, track_count=0):
        self.user_id = user_id
        self.is_premium = is_premium
        self.track_count = track_count


class FakeTrack:
    def __init__(
        self,
        track_id,
        user_id,
        title="Old Title",
        description="Old Desc",
        file_url="old.mp3",
        genre=None,
        tags=None,
        release_date=None,
        visibility=None,
        processing_status="finished",
        play_count=0,
        duration_seconds=None,
        waveform_peaks=None,
        file_hash=None,
        cover_image_url=None,
    ):
        self.track_id = track_id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.file_url = file_url
        self.genre = genre
        self.tags = tags
        self.release_date = release_date
        self.visibility = visibility
        self.processing_status = processing_status
        self.play_count = play_count
        self.duration_seconds = duration_seconds
        self.waveform_peaks = waveform_peaks
        self.file_hash = file_hash
        self.cover_image_url = cover_image_url


class FakeTrackUpdate:
    def __init__(
        self,
        title=None,
        description=None,
        file_url=None,
        genre=None,
        tags=None,
        release_date=None,
        visibility=None,
    ):
        self.title = title
        self.description = description
        self.file_url = file_url
        self.genre = genre
        self.tags = tags
        self.release_date = release_date
        self.visibility = visibility

    def model_dump(self, exclude_unset=False):
        data = {
            "title": self.title,
            "description": self.description,
            "file_url": self.file_url,
            "genre": self.genre,
            "tags": self.tags,
            "release_date": self.release_date,
            "visibility": self.visibility,
        }
        if exclude_unset:
            return {key: value for key, value in data.items() if value is not None}
        return data


class FakeUploadFile:
    def __init__(
        self,
        filename="test.mp3",
        content_type="audio/mpeg",
        content=b"fake mp3 content",
    ):
        self.filename = filename
        self.content_type = content_type
        self.file = BytesIO(content)


def test_create_track(monkeypatch):
    db = FakeDB()
    user = FakeUser(uuid4())
    upload = FakeUploadFile()

    created_tracks = []

    from app.repositories.track_repo import TrackRepository
    from app.services import track_service

    upload_dir = os.path.join("app", "uploads", "test-unit")
    monkeypatch.setattr(track_service, "UPLOAD_DIR", upload_dir)

    def fake_create(db_arg, track):
        created_tracks.append(track)
        if getattr(track, "track_id", None) is None:
            track.track_id = uuid4()

    monkeypatch.setattr(
        TrackRepository,
        "get_by_user_id_and_file_hash",
        lambda db_arg, uid, file_hash: None,
    )
    monkeypatch.setattr(TrackRepository, "create", fake_create)

    result = TrackService.create_track(
        db,
        user,
        "My Song",
        "Test song",
        upload,
        genre="Rock",
        tags="demo, test",
        visibility="private",
    )

    assert result["success"] is True
    assert result["message"] == "Track uploaded successfully."
    assert result["data"]["title"] == "My Song"
    assert "file_url" not in result["data"]
    assert result["data"]["stream_url"].startswith("/api/tracks/")
    assert len(created_tracks) == 1
    assert created_tracks[0].user_id == user.user_id
    assert created_tracks[0].file_hash is not None
    assert created_tracks[0].genre == "Rock"
    assert created_tracks[0].tags == ["demo", "test"]
    assert created_tracks[0].visibility == "private"
    assert created_tracks[0].processing_status == "finished"


def test_create_track_with_cover_image(monkeypatch):
    db = FakeDB()
    user = FakeUser(uuid4())
    audio = FakeUploadFile()
    cover = FakeUploadFile(
        filename="cover.png",
        content_type="image/png",
        content=b"fake image content",
    )
    upload_dir = Path("tmp") / "test-track-service-cover" / str(uuid4())
    created_tracks = []

    from app.repositories.track_repo import TrackRepository
    from app.services import track_service

    monkeypatch.setattr(track_service, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(
        track_service,
        "upload_image",
        lambda file, folder, public_id: "https://fake.cloudinary.com/cover.jpg",
    )
    monkeypatch.setattr(
        TrackRepository,
        "get_by_user_id_and_file_hash",
        lambda db_arg, uid, file_hash: None,
    )

    def fake_create(db_arg, track):
        created_tracks.append(track)
        if getattr(track, "track_id", None) is None:
            track.track_id = uuid4()

    monkeypatch.setattr(TrackRepository, "create", fake_create)

    result = TrackService.create_track(
        db,
        user,
        "Song With Cover",
        "Track artwork test",
        audio,
        visibility="private",
        cover_image=cover,
    )

    assert result["success"] is True
    assert len(created_tracks) == 1
    assert result["data"]["cover_image_url"] == "https://fake.cloudinary.com/cover.jpg"
    assert result["data"]["cover_image_url"] == created_tracks[0].cover_image_url

    saved_audio = upload_dir / Path(created_tracks[0].file_url).name
    assert saved_audio.read_bytes() == b"fake mp3 content"


def test_create_track_rejects_invalid_cover_image_type():
    db = FakeDB()
    user = FakeUser(uuid4())
    audio = FakeUploadFile()
    cover = FakeUploadFile(
        filename="cover.txt",
        content_type="text/plain",
        content=b"not an image",
    )

    with pytest.raises(HTTPException) as exc:
        TrackService.create_track(
            db,
            user,
            "Song",
            "Desc",
            audio,
            cover_image=cover,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Cover image must be JPEG, PNG, WebP, or GIF"


def test_create_track_rejects_invalid_visibility():
    db = FakeDB()
    user = FakeUser(uuid4())
    upload = FakeUploadFile()

    with pytest.raises(HTTPException) as exc:
        TrackService.create_track(
            db,
            user,
            "Song",
            "Desc",
            upload,
            visibility="friends",
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Visibility must be 'public' or 'private'"


def test_create_track_rejects_missing_filename():
    db = FakeDB()
    user = FakeUser(uuid4())
    upload = FakeUploadFile(filename="")

    with pytest.raises(HTTPException) as exc:
        TrackService.create_track(db, user, "Song", "Desc", upload)

    assert exc.value.status_code == 400
    assert exc.value.detail == "No file uploaded"


def test_create_track_rejects_non_audio_file():
    db = FakeDB()
    user = FakeUser(uuid4())
    upload = FakeUploadFile(
        filename="test.txt",
        content_type="text/plain",
        content=b"not audio",
    )

    with pytest.raises(HTTPException) as exc:
        TrackService.create_track(db, user, "Song", "Desc", upload)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Only audio files are allowed"


def test_create_track_rejects_large_file(monkeypatch):
    db = FakeDB()
    user = FakeUser(uuid4())
    upload = FakeUploadFile(content=b"x" * 11)

    from app.services import track_service

    monkeypatch.setattr(track_service, "TRACK_MAX_SIZE", 10)

    with pytest.raises(HTTPException) as exc:
        TrackService.create_track(db, user, "Song", "Desc", upload)

    assert exc.value.status_code == 413
    assert exc.value.detail == "File size must not exceed 100 MB"


def test_create_track_rejects_duplicate_file(monkeypatch):
    db = FakeDB()
    user = FakeUser(uuid4())
    upload = FakeUploadFile(content=b"same audio bytes")
    existing_track = FakeTrack(track_id=uuid4(), user_id=user.user_id)

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(
        TrackRepository,
        "get_by_user_id_and_file_hash",
        lambda db_arg, uid, file_hash: existing_track,
    )

    with pytest.raises(HTTPException) as exc:
        TrackService.create_track(db, user, "Song", "Desc", upload)

    assert exc.value.status_code == 409
    assert exc.value.detail == "You already uploaded this track"


def test_get_track_by_id_found(monkeypatch):
    db = FakeDB()
    track_id = uuid4()
    track = FakeTrack(track_id=track_id, user_id=uuid4())

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    result = TrackService.get_track_by_id(db, track_id)

    assert result == track


def test_get_track_by_id_not_found(monkeypatch):
    db = FakeDB()
    track_id = uuid4()

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: None)

    result = TrackService.get_track_by_id(db, track_id)

    assert result is None


def test_get_tracks_by_user_returns_public_tracks_for_non_owner(monkeypatch):
    db = FakeDB()
    user_id = uuid4()
    viewer = FakeUser(uuid4())
    public_track = FakeTrack(track_id=uuid4(), user_id=user_id, visibility="public")
    repo_calls = []

    from app.repositories.track_repo import TrackRepository
    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: FakeUser(uid))

    def fake_get_by_user_id(db_arg, uid, include_private=False):
        repo_calls.append(
            {
                "user_id": uid,
                "include_private": include_private,
            }
        )
        return [public_track]

    monkeypatch.setattr(TrackRepository, "get_by_user_id", fake_get_by_user_id)

    result = TrackService.get_tracks_by_user(db, user_id, viewer)

    assert result["success"] is True
    assert result["data"]["user_id"] == str(user_id)
    assert len(result["data"]["tracks"]) == 1
    assert result["data"]["tracks"][0]["track_id"] == str(public_track.track_id)
    assert repo_calls == [{"user_id": user_id, "include_private": False}]


def test_get_tracks_by_user_returns_private_tracks_for_owner(monkeypatch):
    db = FakeDB()
    user_id = uuid4()
    owner = FakeUser(user_id)
    private_track = FakeTrack(track_id=uuid4(), user_id=user_id, visibility="private")
    repo_calls = []

    from app.repositories.track_repo import TrackRepository
    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: FakeUser(uid))

    def fake_get_by_user_id(db_arg, uid, include_private=False):
        repo_calls.append(
            {
                "user_id": uid,
                "include_private": include_private,
            }
        )
        return [private_track]

    monkeypatch.setattr(TrackRepository, "get_by_user_id", fake_get_by_user_id)

    result = TrackService.get_tracks_by_user(db, user_id, owner)

    assert result["success"] is True
    assert result["data"]["tracks"][0]["visibility"] == "private"
    assert repo_calls == [{"user_id": user_id, "include_private": True}]


def test_get_tracks_by_user_not_found(monkeypatch):
    db = FakeDB()
    user_id = uuid4()

    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: None)

    with pytest.raises(HTTPException) as exc:
        TrackService.get_tracks_by_user(db, user_id)

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"


def test_get_liked_tracks_by_user_returns_public_tracks_for_non_owner(monkeypatch):
    db = FakeDB()
    user_id = uuid4()
    viewer = FakeUser(uuid4())
    public_track = FakeTrack(track_id=uuid4(), user_id=uuid4(), visibility="public")
    repo_calls = []

    from app.repositories.like_repo import LikeRepository
    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: FakeUser(uid))

    def fake_get_liked_tracks(db_arg, uid, include_private=False):
        repo_calls.append(
            {
                "user_id": uid,
                "include_private": include_private,
            }
        )
        return [public_track]

    monkeypatch.setattr(
        LikeRepository,
        "get_liked_tracks_by_user",
        fake_get_liked_tracks,
    )

    result = TrackService.get_liked_tracks_by_user(db, user_id, viewer)

    assert result["success"] is True
    assert result["data"]["user_id"] == str(user_id)
    assert len(result["data"]["tracks"]) == 1
    assert result["data"]["tracks"][0]["track_id"] == str(public_track.track_id)
    assert repo_calls == [{"user_id": user_id, "include_private": False}]


def test_get_liked_tracks_by_user_returns_private_tracks_for_owner(monkeypatch):
    db = FakeDB()
    user_id = uuid4()
    owner = FakeUser(user_id)
    private_track = FakeTrack(track_id=uuid4(), user_id=uuid4(), visibility="private")
    repo_calls = []

    from app.repositories.like_repo import LikeRepository
    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: FakeUser(uid))

    def fake_get_liked_tracks(db_arg, uid, include_private=False):
        repo_calls.append(
            {
                "user_id": uid,
                "include_private": include_private,
            }
        )
        return [private_track]

    monkeypatch.setattr(
        LikeRepository,
        "get_liked_tracks_by_user",
        fake_get_liked_tracks,
    )

    result = TrackService.get_liked_tracks_by_user(db, user_id, owner)

    assert result["success"] is True
    assert result["data"]["tracks"][0]["visibility"] == "private"
    assert repo_calls == [{"user_id": user_id, "include_private": True}]


def test_get_liked_tracks_by_user_not_found(monkeypatch):
    db = FakeDB()
    user_id = uuid4()

    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: None)

    with pytest.raises(HTTPException) as exc:
        TrackService.get_liked_tracks_by_user(db, user_id)

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"


def test_update_track_success(monkeypatch):
    db = FakeDB()
    owner_id = uuid4()
    track_id = uuid4()
    track = FakeTrack(track_id=track_id, user_id=owner_id)

    from app.repositories.track_repo import TrackRepository
    from app.services import track_service

    upload_dir = Path("tmp") / "test-track-service" / str(uuid4())
    upload_dir.mkdir(parents=True, exist_ok=True)
    audio_file = upload_dir / "new.mp3"
    audio_file.write_bytes(b"fake audio")
    monkeypatch.setattr(track_service, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    update_data = FakeTrackUpdate(
        title="New Title",
        description="New Description",
        genre="Pop",
        tags=["new", "single"],
        file_url="new.mp3",
        visibility="public",
    )

    result = TrackService.update_track(db, track_id, update_data, owner_id)

    assert result == track
    assert track.title == "New Title"
    assert track.description == "New Description"
    assert track.genre == "Pop"
    assert track.tags == ["new", "single"]
    assert track.file_url == "new.mp3"
    assert track.visibility == "public"
    assert track.waveform_peaks is None
    assert track.duration_seconds is None
    assert db.committed is True
    assert db.refreshed == track


def test_update_track_rejects_missing_audio_file(monkeypatch):
    db = FakeDB()
    owner_id = uuid4()
    track_id = uuid4()
    track = FakeTrack(track_id=track_id, user_id=owner_id)

    from app.repositories.track_repo import TrackRepository
    from app.services import track_service

    upload_dir = Path("tmp") / "test-track-service" / str(uuid4())
    upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(track_service, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    update_data = FakeTrackUpdate(file_url="missing.mp3")

    with pytest.raises(HTTPException) as exc:
        TrackService.update_track(db, track_id, update_data, owner_id)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Audio file does not exist in uploads"


def test_update_track_not_found(monkeypatch):
    db = FakeDB()
    track_id = uuid4()

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: None)

    update_data = FakeTrackUpdate(title="Anything")

    result = TrackService.update_track(db, track_id, update_data, uuid4())

    assert result is None


def test_update_track_forbidden(monkeypatch):
    db = FakeDB()
    owner_id = uuid4()
    other_user_id = uuid4()
    track_id = uuid4()
    track = FakeTrack(track_id=track_id, user_id=owner_id)

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    update_data = FakeTrackUpdate(title="Hack")

    result = TrackService.update_track(db, track_id, update_data, other_user_id)

    assert result == "forbidden"


def test_delete_track_success(monkeypatch):
    db = FakeDB()
    owner_id = uuid4()
    track_id = uuid4()
    user = FakeUser(owner_id)
    track = FakeTrack(track_id=track_id, user_id=owner_id)

    from app.repositories.track_repo import TrackRepository
    from app.repositories.playlist_repo import PlaylistRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)
    monkeypatch.setattr(
        PlaylistRepository,
        "get_playlist_tracks_by_track",
        lambda db_arg, tid: ["pt1", "pt2"],
    )

    result = TrackService.delete_track(db, user, track_id)

    assert result["success"] is True
    assert result["message"] == "Track deleted successfully"
    assert len(db.deleted) == 3
    assert track in db.deleted
    assert db.committed is True


def test_delete_track_not_found(monkeypatch):
    db = FakeDB()
    user = FakeUser(uuid4())
    track_id = uuid4()

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: None)

    with pytest.raises(HTTPException) as exc:
        TrackService.delete_track(db, user, track_id)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Track not found"


def test_delete_track_forbidden(monkeypatch):
    db = FakeDB()
    owner_id = uuid4()
    other_user_id = uuid4()
    track_id = uuid4()
    user = FakeUser(other_user_id)
    track = FakeTrack(track_id=track_id, user_id=owner_id)

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    with pytest.raises(HTTPException) as exc:
        TrackService.delete_track(db, user, track_id)

    assert exc.value.status_code == 403
    assert exc.value.detail == "You can only delete your own tracks"


def test_admin_delete_track_success(monkeypatch):
    db = FakeDB()
    track_id = uuid4()
    track = FakeTrack(track_id=track_id, user_id=uuid4())

    from app.repositories.track_repo import TrackRepository
    from app.repositories.playlist_repo import PlaylistRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)
    monkeypatch.setattr(
        PlaylistRepository,
        "get_playlist_tracks_by_track",
        lambda db_arg, tid: ["pt1"],
    )

    result = TrackService.admin_delete_track(db, track_id)

    assert result == track
    assert len(db.deleted) == 2
    assert track in db.deleted
    assert db.committed is True


def test_get_track_details_rejects_private_for_non_owner(monkeypatch):
    db = FakeDB()
    track_id = uuid4()
    track = FakeTrack(
        track_id=track_id,
        user_id=uuid4(),
        visibility="private",
    )

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    with pytest.raises(HTTPException) as exc:
        TrackService.get_track_details(db, track_id, None)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Track is private"


def test_get_stream_success(monkeypatch):
    db = FakeDB()
    track_id = uuid4()
    track = FakeTrack(
        track_id=track_id,
        user_id=uuid4(),
        file_url="http://127.0.0.1:8000/api/uploads/song.mp3",
        play_count=7,
    )

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    result = TrackService.get_stream(db, track_id)

    assert result["success"] is True
    assert result["data"]["stream_url"] == f"/api/tracks/{track_id}/audio"
    assert result["data"]["play_count"] == 7
    assert result["data"]["expires_in"] is None


def test_record_play_increments_count(monkeypatch):
    db = FakeDB()
    track_id = uuid4()
    track = FakeTrack(track_id=track_id, user_id=uuid4(), play_count=2)

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    result = TrackService.record_play(db, track_id)

    assert result["success"] is True
    assert result["data"]["play_count"] == 3
    assert track.play_count == 3
    assert db.committed is True
    assert db.refreshed == track


def test_record_play_creates_history_for_authenticated_user(monkeypatch):
    db = FakeDB()
    user = FakeUser(uuid4())
    track_id = uuid4()
    track = FakeTrack(track_id=track_id, user_id=uuid4(), play_count=2)

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    result = TrackService.record_play(db, track_id, user, 30)

    assert result["success"] is True
    assert result["data"]["play_count"] == 3
    assert len(db.added) == 1
    assert db.added[0].user_id == user.user_id
    assert db.added[0].track_id == track_id
    assert db.added[0].duration_listened_seconds == 30


def test_get_waveform_returns_cached_peaks(monkeypatch):
    db = FakeDB()
    track_id = uuid4()
    track = FakeTrack(
        track_id=track_id,
        user_id=uuid4(),
        duration_seconds=12,
        waveform_peaks=[0.1, 0.5, 0.2],
    )

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    result = TrackService.get_waveform(db, track_id)

    assert result["success"] is True
    assert result["data"]["duration_seconds"] == 12
    assert result["data"]["sample_count"] == 3
    assert result["data"]["peaks"] == [0.1, 0.5, 0.2]


def test_get_playback_success_with_cached_waveform(monkeypatch):
    db = FakeDB()
    track_id = uuid4()
    track = FakeTrack(
        track_id=track_id,
        user_id=uuid4(),
        title="Player Song",
        description="Ready for playback",
        file_url="http://127.0.0.1:8000/api/uploads/player.mp3",
        play_count=4,
        duration_seconds=33,
        waveform_peaks=[0.2, 0.8],
    )

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    result = TrackService.get_playback(db, track_id)

    assert result["success"] is True
    assert result["data"]["title"] == "Player Song"
    assert result["data"]["stream_url"] == f"/api/tracks/{track_id}/audio"
    assert result["data"]["play_count"] == 4
    assert result["data"]["duration_seconds"] == 33
    assert result["data"]["waveform"]["peaks"] == [0.2, 0.8]


def test_get_listening_history_success(monkeypatch):
    db = FakeDB()
    user = FakeUser(uuid4())
    history_id = uuid4()
    track_id = uuid4()

    class FakeHistory:
        def __init__(self):
            self.history_id = history_id
            self.played_at = datetime(2026, 4, 13, tzinfo=timezone.utc)
            self.duration_listened_seconds = 25

    track = FakeTrack(
        track_id=track_id,
        user_id=uuid4(),
        title="History Song",
        description="From history",
        file_url="http://127.0.0.1:8000/api/uploads/history.mp3",
        play_count=9,
        duration_seconds=120,
    )

    from app.repositories.listening_history_repo import ListeningHistoryRepository

    monkeypatch.setattr(
        ListeningHistoryRepository,
        "get_by_user_id",
        lambda db_arg, uid, limit: [(FakeHistory(), track)],
    )

    result = TrackService.get_listening_history(db, user, 10)

    assert result["success"] is True
    item = result["data"]["items"][0]
    assert item["history_id"] == str(history_id)
    assert item["duration_listened_seconds"] == 25
    assert item["track"]["title"] == "History Song"

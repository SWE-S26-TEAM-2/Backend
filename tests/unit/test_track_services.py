from uuid import uuid4
import pytest
from fastapi import HTTPException

from app.services.track_service import TrackService


class FakeDB:
    def __init__(self):
        self.deleted = []
        self.committed = False
        self.refreshed = None

    def delete(self, obj):
        self.deleted.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed = obj


class FakeUser:
    def __init__(self, user_id):
        self.user_id = user_id


class FakeTrack:
    def __init__(
        self,
        track_id,
        user_id,
        title="Old Title",
        description="Old Desc",
        file_url="old.mp3",
        visibility=None,
    ):
        self.track_id = track_id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.file_url = file_url
        self.visibility = visibility


class FakeTrackCreate:
    def __init__(self, title, description, file_url):
        self.title = title
        self.description = description
        self.file_url = file_url


class FakeTrackUpdate:
    def __init__(self, title=None, description=None, file_url=None, visibility=None):
        self.title = title
        self.description = description
        self.file_url = file_url
        self.visibility = visibility


def test_create_track(monkeypatch):
    db = FakeDB()
    user = FakeUser(uuid4())
    data = FakeTrackCreate(
        title="My Song",
        description="Test song",
        file_url="https://example.com/test.mp3",
    )

    created_tracks = []

    from app.repositories.track_repo import TrackRepository

    def fake_create(db_arg, track):
        created_tracks.append(track)
        if getattr(track, "track_id", None) is None:
            track.track_id = uuid4()

    monkeypatch.setattr(TrackRepository, "create", fake_create)

    result = TrackService.create_track(db, user, data)

    assert result["success"] is True
    assert result["message"] == "Track created successfully."
    assert result["data"]["title"] == "My Song"
    assert len(created_tracks) == 1
    assert created_tracks[0].user_id == user.user_id


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


def test_update_track_success(monkeypatch):
    db = FakeDB()
    owner_id = uuid4()
    track_id = uuid4()
    track = FakeTrack(track_id=track_id, user_id=owner_id)

    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db_arg, tid: track)

    update_data = FakeTrackUpdate(
        title="New Title",
        description="New Description",
        file_url="new.mp3",
        visibility="public",
    )

    result = TrackService.update_track(db, track_id, update_data, owner_id)

    assert result == track
    assert track.title == "New Title"
    assert track.description == "New Description"
    assert track.file_url == "new.mp3"
    assert track.visibility == "public"
    assert db.committed is True
    assert db.refreshed == track


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

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.services.track_service import TrackService
from tests.unit.test_track_services import FakeTrack

client = TestClient(app)


class FakeUser:
    def __init__(self, user_id):
        self.user_id = user_id


class DummyDB:
    pass


def override_get_db():
    yield DummyDB()


def setup_module(module):
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(module):
    app.dependency_overrides.clear()


def test_get_track_success(monkeypatch):
    track_id = uuid4()

    fake_track = FakeTrack(
        track_id=track_id,
        user_id=uuid4(),
        title="Demo Track",
        description="Demo description",
        file_url="https://example.com/demo.mp3",
        visibility="public",
    )

    monkeypatch.setattr(
        TrackService,
        "get_track_details",
        lambda db, tid, user=None: {
            "success": True,
            "data": {
                "track_id": str(fake_track.track_id),
                "title": fake_track.title,
                "description": fake_track.description,
                "file_url": fake_track.file_url,
                "user_id": str(fake_track.user_id),
                "visibility": fake_track.visibility,
            },
        },
    )

    response = client.get(f"/tracks/{track_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Demo Track"


def test_get_track_not_found(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        TrackService,
        "get_track_details",
        lambda db, tid, user=None: (_ for _ in ()).throw(
            HTTPException(status_code=404, detail="Track not found")
        ),
    )

    response = client.get(f"/tracks/{track_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found"


def test_update_track_success(monkeypatch):
    track_id = uuid4()
    user_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    updated_track = FakeTrack(
        track_id=track_id,
        user_id=user_id,
        title="Updated Title",
        description="Updated Description",
        file_url="updated.mp3",
        visibility="public",
    )

    monkeypatch.setattr(
        TrackService,
        "update_track",
        lambda db, tid, track_data, uid: updated_track,
    )

    response = client.put(
        f"/tracks/{track_id}",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "file_url": "updated.mp3",
            "visibility": "public",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Updated Title"

    app.dependency_overrides.pop(get_current_user, None)


def test_update_track_not_found(monkeypatch):
    track_id = uuid4()
    user_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    monkeypatch.setattr(
        TrackService,
        "update_track",
        lambda db, tid, track_data, uid: None,
    )

    response = client.put(
        f"/tracks/{track_id}",
        json={"title": "Anything"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found"

    app.dependency_overrides.pop(get_current_user, None)


def test_update_track_forbidden(monkeypatch):
    track_id = uuid4()
    user_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    monkeypatch.setattr(
        TrackService,
        "update_track",
        lambda db, tid, track_data, uid: "forbidden",
    )

    response = client.put(
        f"/tracks/{track_id}",
        json={"title": "Hack"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not Authorized to update this track"

    app.dependency_overrides.pop(get_current_user, None)


def test_create_track_success(monkeypatch):
    user_id = uuid4()
    track_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)
    app.dependency_overrides[get_db] = override_get_db

    def fake_create_track(
        db,
        user,
        title,
        description,
        file,
        genre=None,
        tags=None,
        release_date=None,
        visibility="public",
    ):
        return {
            "success": True,
            "message": "Track uploaded successfully.",
            "data": {
                "track_id": str(track_id),
                "title": title,
                "file_url": "http://127.0.0.1:8000/uploads/test.mp3",
            },
        }

    monkeypatch.setattr(
        TrackService,
        "create_track",
        fake_create_track,
    )

    response = client.post(
        "/tracks/",
        data={
            "title": "My New Track",
            "description": "Testing create",
        },
        files={
            "file": ("test.mp3", b"fake mp3 content", "audio/mpeg"),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Track uploaded successfully."
    assert body["data"]["track_id"] == str(track_id)
    assert body["data"]["title"] == "My New Track"

    app.dependency_overrides.clear()


def test_create_track_validation_error():
    user_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)
    app.dependency_overrides[get_db] = override_get_db

    response = client.post(
        "/tracks/",
        data={
            "description": "Missing title and file",
        },
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_delete_track_success(monkeypatch):
    user_id = uuid4()
    track_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)
    app.dependency_overrides[get_db] = override_get_db

    monkeypatch.setattr(
        TrackService,
        "delete_track",
        lambda db, user, tid: {
            "success": True,
            "message": "Track deleted successfully",
        },
    )

    response = client.delete(f"/tracks/{track_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Track deleted successfully"

    app.dependency_overrides.clear()


def test_delete_track_not_found(monkeypatch):
    user_id = uuid4()
    track_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)
    app.dependency_overrides[get_db] = override_get_db

    def fake_delete(db, user, tid):
        raise HTTPException(status_code=404, detail="Track not found")

    monkeypatch.setattr(TrackService, "delete_track", fake_delete)

    response = client.delete(f"/tracks/{track_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found"

    app.dependency_overrides.clear()


def test_delete_track_forbidden(monkeypatch):
    user_id = uuid4()
    track_id = uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)
    app.dependency_overrides[get_db] = override_get_db

    def fake_delete(db, user, tid):
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own tracks",
        )

    monkeypatch.setattr(TrackService, "delete_track", fake_delete)

    response = client.delete(f"/tracks/{track_id}")

    assert response.status_code == 403
    assert response.json()["detail"] == "You can only delete your own tracks"

    app.dependency_overrides.clear()


def test_get_track_waveform_success(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        TrackService,
        "get_waveform",
        lambda db, tid, user=None: {
            "success": True,
            "data": {
                "track_id": str(track_id),
                "duration_seconds": 10,
                "sample_count": 2,
                "peaks": [0.1, 0.3],
            },
        },
    )

    response = client.get(f"/tracks/{track_id}/waveform")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["sample_count"] == 2


def test_get_track_stream_success(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        TrackService,
        "get_stream",
        lambda db, tid, user=None: {
            "success": True,
            "data": {
                "track_id": str(track_id),
                "stream_url": f"/api/tracks/{track_id}/audio",
                "expires_in": None,
                "content_type": "audio/mpeg",
                "play_count": 5,
            },
        },
    )

    response = client.get(f"/tracks/{track_id}/stream")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["play_count"] == 5


def test_stream_track_audio_supports_range_requests(monkeypatch):
    track_id = uuid4()
    audio_dir = Path("tmp") / "test-audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_file = audio_dir / "range-test.mp3"
    audio_file.write_bytes(b"0123456789")

    fake_track = FakeTrack(
        track_id=track_id,
        user_id=uuid4(),
        file_url=f"http://127.0.0.1:8000/api/uploads/{audio_file.name}",
        visibility="public",
    )

    from app.repositories.track_repo import TrackRepository
    from app.services import track_service

    monkeypatch.setattr(track_service, "UPLOAD_DIR", str(audio_dir))
    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db, tid: fake_track)

    response = client.get(
        f"/tracks/{track_id}/audio",
        headers={"Range": "bytes=0-3"},
    )

    assert response.status_code == 206
    assert response.content == b"0123"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-range"] == "bytes 0-3/10"
    assert response.headers["content-length"] == "4"


def test_record_track_play_success(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        TrackService,
        "record_play",
        lambda db, tid, user=None, duration_listened_seconds=None: {
            "success": True,
            "message": "Play recorded successfully.",
            "data": {
                "track_id": str(track_id),
                "play_count": 6,
            },
        },
    )

    response = client.post(f"/tracks/{track_id}/plays")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["play_count"] == 6


def test_get_recently_played_success(monkeypatch):
    user_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    monkeypatch.setattr(
        TrackService,
        "get_listening_history",
        lambda db, user, limit: {
            "success": True,
            "data": {
                "items": [
                    {
                        "history_id": str(uuid4()),
                        "played_at": "2026-04-13T00:00:00+00:00",
                        "duration_listened_seconds": 20,
                        "track": {
                            "track_id": str(uuid4()),
                            "title": "Recent Song",
                            "file_url": "test.mp3",
                            "duration_seconds": 100,
                            "play_count": 3,
                        },
                    }
                ]
            },
        },
    )

    response = client.get("/users/me/recently-played?limit=10")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["items"][0]["track"]["title"] == "Recent Song"

    app.dependency_overrides.clear()


def test_get_listening_history_success(monkeypatch):
    user_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    monkeypatch.setattr(
        TrackService,
        "get_listening_history",
        lambda db, user, limit: {
            "success": True,
            "data": {"items": []},
        },
    )

    response = client.get("/users/me/listening-history")

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []

    app.dependency_overrides.clear()


def test_get_track_playback_success(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        TrackService,
        "get_playback",
        lambda db, tid, user=None: {
            "success": True,
            "data": {
                "track_id": str(track_id),
                "title": "Player Song",
                "stream_url": "http://127.0.0.1:8000/api/uploads/test.mp3",
                "play_count": 1,
                "duration_seconds": 10,
                "waveform": {
                    "sample_count": 2,
                    "peaks": [0.2, 0.4],
                },
            },
        },
    )

    response = client.get(f"/tracks/{track_id}/playback")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["waveform"]["peaks"] == [0.2, 0.4]


def test_create_track_json_validation_error():
    user_id = str(uuid4())

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)
    app.dependency_overrides[get_db] = override_get_db

    response = client.post(
        "/tracks/",
        json={"description": "Missing title and file_url"},
    )

    assert response.status_code == 422

    app.dependency_overrides.clear()

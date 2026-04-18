"""
Unit tests for the Playlist Router endpoints.

Tests all API endpoints with TestClient, including:
- POST /playlists/ - Create playlist
- GET /playlists/{playlist_id} - Get playlist
- PATCH /playlists/{playlist_id} - Update playlist
- DELETE /playlists/{playlist_id} - Delete playlist
- POST /playlists/{playlist_id}/tracks - Add track to playlist
- DELETE /playlists/{playlist_id}/tracks/{track_id} - Remove track from playlist
"""

import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.services.playlist_service import PlaylistService

client = TestClient(app)


class FakeUser:
    """Mock user for dependency override."""

    def __init__(self, user_id=None):
        self.user_id = user_id or uuid.uuid4()


class DummyDB:
    """Mock database for dependency override."""

    pass


def override_get_db():
    """Override database dependency."""
    yield DummyDB()


def setup_module(module):
    """Setup test fixtures before running tests."""
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(module):
    """Cleanup after tests."""
    app.dependency_overrides.clear()


# ────────────────────────────────────────────────────────
# CREATE PLAYLIST ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_create_playlist_endpoint_success(monkeypatch):
    """Test POST /playlists/ returns 200 with success response."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    def fake_create_playlist(db, user, data):
        return {
            "success": True,
            "message": "Playlist created successfully.",
            "data": {
                "playlist_id": str(playlist_id),
                "name": data.name,
                "description": data.description,
            },
        }

    monkeypatch.setattr(PlaylistService, "create_playlist", fake_create_playlist)

    response = client.post(
        "/playlists/",
        json={
            "name": "My Playlist",
            "description": "My favorite songs",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Playlist created successfully."
    assert body["data"]["name"] == "My Playlist"
    assert body["data"]["description"] == "My favorite songs"


def test_create_playlist_endpoint_without_auth(monkeypatch):
    """Test POST /playlists/ without authentication returns 401 or 403."""
    # Clear the override to simulate no user
    app.dependency_overrides.pop(get_current_user, None)

    response = client.post(
        "/playlists/",
        json={
            "name": "My Playlist",
            "description": "My favorite songs",
        },
    )

    # Should fail due to missing authentication
    assert response.status_code in [401, 403]

    app.dependency_overrides[get_current_user] = lambda: FakeUser()


def test_create_playlist_endpoint_missing_name(monkeypatch):
    """Test POST /playlists/ with missing name field."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    response = client.post(
        "/playlists/",
        json={
            "description": "My favorite songs",
        },
    )

    # Should fail due to validation error
    assert response.status_code >= 400


def test_create_playlist_endpoint_with_None_description(monkeypatch):
    """Test POST /playlists/ with null description."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    def fake_create_playlist(db, user, data):
        return {
            "success": True,
            "message": "Playlist created successfully.",
            "data": {
                "playlist_id": str(playlist_id),
                "name": data.name,
                "description": data.description,
            },
        }

    monkeypatch.setattr(PlaylistService, "create_playlist", fake_create_playlist)

    response = client.post(
        "/playlists/",
        json={
            "name": "Simple Playlist",
            "description": None,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["name"] == "Simple Playlist"
    assert body["data"]["description"] is None


# ────────────────────────────────────────────────────────
# GET PLAYLIST ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_get_playlist_endpoint_success(monkeypatch):
    """Test GET /playlists/{playlist_id} returns 200 with playlist data."""
    playlist_id = uuid.uuid4()
    user_id = uuid.uuid4()

    def fake_get_playlist(db, pid):
        return {
            "success": True,
            "data": {
                "playlist_id": str(playlist_id),
                "user_id": str(user_id),
                "name": "My Playlist",
                "description": "My description",
                "tracks": [],
            },
        }

    monkeypatch.setattr(PlaylistService, "get_playlist", fake_get_playlist)

    response = client.get(f"/playlists/{playlist_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "My Playlist"
    assert body["data"]["playlist_id"] == str(playlist_id)


def test_get_playlist_endpoint_not_found(monkeypatch):
    """Test GET /playlists/{playlist_id} returns 404 for non-existent playlist."""
    playlist_id = uuid.uuid4()

    from fastapi import HTTPException, status

    def fake_get_playlist(db, pid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found",
        )

    monkeypatch.setattr(PlaylistService, "get_playlist", fake_get_playlist)

    response = client.get(f"/playlists/{playlist_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Playlist not found"


def test_get_playlist_endpoint_invalid_id_format(monkeypatch):
    """Test GET /playlists/{invalid_id} with invalid UUID format."""
    response = client.get("/playlists/invalid-uuid")

    # Should fail validation
    assert response.status_code >= 400


# ────────────────────────────────────────────────────────
# UPDATE PLAYLIST ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_update_playlist_endpoint_success(monkeypatch):
    """Test PATCH /playlists/{playlist_id} returns 200 with updated data."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    def fake_update_playlist(db, user, pid, data):
        return {
            "success": True,
            "message": "Playlist updated successfully.",
            "data": {
                "playlist_id": str(playlist_id),
                "name": "Updated Name",
                "description": "Updated Description",
            },
        }

    monkeypatch.setattr(PlaylistService, "update_playlist", fake_update_playlist)

    response = client.patch(
        f"/playlists/{playlist_id}",
        json={
            "name": "Updated Name",
            "description": "Updated Description",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Updated Name"


def test_update_playlist_endpoint_unauthorized(monkeypatch):
    """Test PATCH /playlists/{playlist_id} returns 403 for non-owner."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_update_playlist(db, user, pid, data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own playlists",
        )

    monkeypatch.setattr(PlaylistService, "update_playlist", fake_update_playlist)

    response = client.patch(f"/playlists/{playlist_id}", json={"name": "Hacked Name"})

    assert response.status_code == 403
    assert response.json()["detail"] == "You can only update your own playlists"


def test_update_playlist_endpoint_not_found(monkeypatch):
    """Test PATCH /playlists/{playlist_id} returns 404 for non-existent playlist."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_update_playlist(db, user, pid, data):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found",
        )

    monkeypatch.setattr(PlaylistService, "update_playlist", fake_update_playlist)

    response = client.patch(f"/playlists/{playlist_id}", json={"name": "New Name"})

    assert response.status_code == 404


def test_update_playlist_endpoint_only_name(monkeypatch):
    """Test PATCH /playlists/{playlist_id} updating only the name."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    def fake_update_playlist(db, user, pid, data):
        return {
            "success": True,
            "message": "Playlist updated successfully.",
            "data": {
                "playlist_id": str(playlist_id),
                "name": "Only Name Updated",
                "description": "Old Description",
            },
        }

    monkeypatch.setattr(PlaylistService, "update_playlist", fake_update_playlist)

    response = client.patch(
        f"/playlists/{playlist_id}", json={"name": "Only Name Updated"}
    )

    assert response.status_code == 200


# ────────────────────────────────────────────────────────
# DELETE PLAYLIST ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_delete_playlist_endpoint_success(monkeypatch):
    """Test DELETE /playlists/{playlist_id} returns 200 success."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    def fake_delete_playlist(db, user, pid):
        return {
            "success": True,
            "message": "Playlist deleted successfully.",
        }

    monkeypatch.setattr(PlaylistService, "delete_playlist", fake_delete_playlist)

    response = client.delete(f"/playlists/{playlist_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Playlist deleted successfully."


def test_delete_playlist_endpoint_unauthorized(monkeypatch):
    """Test DELETE /playlists/{playlist_id} returns 403 for non-owner."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_delete_playlist(db, user, pid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own playlists",
        )

    monkeypatch.setattr(PlaylistService, "delete_playlist", fake_delete_playlist)

    response = client.delete(f"/playlists/{playlist_id}")

    assert response.status_code == 403


def test_delete_playlist_endpoint_not_found(monkeypatch):
    """Test DELETE /playlists/{playlist_id} returns 404 for non-existent playlist."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_delete_playlist(db, user, pid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found",
        )

    monkeypatch.setattr(PlaylistService, "delete_playlist", fake_delete_playlist)

    response = client.delete(f"/playlists/{playlist_id}")

    assert response.status_code == 404


# ────────────────────────────────────────────────────────
# ADD TRACK TO PLAYLIST ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_add_track_to_playlist_endpoint_success(monkeypatch):
    """Test POST /playlists/{playlist_id}/tracks returns 200."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    def fake_add_track(db, user, pid, data):
        return {
            "success": True,
            "message": "Track added to playlist successfully.",
        }

    monkeypatch.setattr(PlaylistService, "add_track_to_playlist", fake_add_track)

    response = client.post(
        f"/playlists/{playlist_id}/tracks", json={"track_id": str(track_id)}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Track added to playlist successfully."


def test_add_track_playlist_not_found(monkeypatch):
    """Test POST /playlists/{playlist_id}/tracks returns 404 if
    playlist doesn't exist."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_add_track(db, user, pid, data):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found",
        )

    monkeypatch.setattr(PlaylistService, "add_track_to_playlist", fake_add_track)

    response = client.post(
        f"/playlists/{playlist_id}/tracks", json={"track_id": str(track_id)}
    )

    assert response.status_code == 404


def test_add_track_unauthorized(monkeypatch):
    """Test POST /playlists/{playlist_id}/tracks returns 403 for non-owner."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_add_track(db, user, pid, data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own playlists",
        )

    monkeypatch.setattr(PlaylistService, "add_track_to_playlist", fake_add_track)

    response = client.post(
        f"/playlists/{playlist_id}/tracks", json={"track_id": str(track_id)}
    )

    assert response.status_code == 403


def test_add_track_not_found(monkeypatch):
    """Test POST /playlists/{playlist_id}/tracks returns 404 if track doesn't exist."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_add_track(db, user, pid, data):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )

    monkeypatch.setattr(PlaylistService, "add_track_to_playlist", fake_add_track)

    response = client.post(
        f"/playlists/{playlist_id}/tracks", json={"track_id": str(track_id)}
    )

    assert response.status_code == 404


def test_add_track_duplicate(monkeypatch):
    """Test POST /playlists/{playlist_id}/tracks returns 409 for duplicate track."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_add_track(db, user, pid, data):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Track already exists in playlist",
        )

    monkeypatch.setattr(PlaylistService, "add_track_to_playlist", fake_add_track)

    response = client.post(
        f"/playlists/{playlist_id}/tracks", json={"track_id": str(track_id)}
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Track already exists in playlist"


# ────────────────────────────────────────────────────────
# REMOVE TRACK FROM PLAYLIST ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_remove_track_from_playlist_endpoint_success(monkeypatch):
    """Test DELETE /playlists/{playlist_id}/tracks/{track_id} returns 200."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    def fake_remove_track(db, user, pid, tid):
        return {
            "success": True,
            "message": "Track removed from playlist successfully.",
        }

    monkeypatch.setattr(
        PlaylistService, "remove_track_from_playlist", fake_remove_track
    )

    response = client.delete(f"/playlists/{playlist_id}/tracks/{track_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Track removed from playlist successfully."


def test_remove_track_playlist_not_found(monkeypatch):
    """Test DELETE /playlists/{playlist_id}/tracks/{track_id} returns 404 if
    playlist doesn't exist."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_remove_track(db, user, pid, tid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found",
        )

    monkeypatch.setattr(
        PlaylistService, "remove_track_from_playlist", fake_remove_track
    )

    response = client.delete(f"/playlists/{playlist_id}/tracks/{track_id}")

    assert response.status_code == 404


def test_remove_track_unauthorized(monkeypatch):
    """Test DELETE /playlists/{playlist_id}/tracks/{track_id} returns 403 for
    non-owner."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_remove_track(db, user, pid, tid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own playlists",
        )

    monkeypatch.setattr(
        PlaylistService, "remove_track_from_playlist", fake_remove_track
    )

    response = client.delete(f"/playlists/{playlist_id}/tracks/{track_id}")

    assert response.status_code == 403


def test_remove_track_not_in_playlist(monkeypatch):
    """Test DELETE /playlists/{playlist_id}/tracks/{track_id} returns 404 if
    track not in playlist."""
    user_id = uuid.uuid4()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id)

    from fastapi import HTTPException, status

    def fake_remove_track(db, user, pid, tid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found in playlist",
        )

    monkeypatch.setattr(
        PlaylistService, "remove_track_from_playlist", fake_remove_track
    )

    response = client.delete(f"/playlists/{playlist_id}/tracks/{track_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Track not found in playlist"

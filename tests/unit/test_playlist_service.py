"""
Unit tests for the Playlist Service.

Tests all endpoints and scenarios including:
- Create playlist (success, with/without description)
- Get playlist (found, not found)
- Update playlist (success, not found, unauthorized, no fields)
- Delete playlist (success, not found, unauthorized)
- Add track to playlist (multiple scenarios)
- Remove track from playlist (multiple scenarios)
"""
import uuid
import pytest
from fastapi import HTTPException

from app.services.playlist_service import PlaylistService


class FakeDB:
    """Mock database session."""
    def __init__(self):
        self.deleted = []
        self.committed = False
        self.refreshed = None
        self.added = []

    def delete(self, obj):
        self.deleted.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed = obj

    def add(self, obj):
        self.added.append(obj)


class FakeUser:
    """Mock user object."""
    def __init__(self, user_id=None):
        self.user_id = user_id or uuid.uuid4()


class FakePlaylist:
    """Mock playlist object."""
    def __init__(self, playlist_id=None, user_id=None, name="Test Playlist", description="Test Description"):
        self.playlist_id = playlist_id or uuid.uuid4()
        self.user_id = user_id or uuid.uuid4()
        self.name = name
        self.description = description


class FakeTrack:
    """Mock track object."""
    def __init__(self, track_id=None, user_id=None):
        self.track_id = track_id or uuid.uuid4()
        self.user_id = user_id or uuid.uuid4()
        self.title = "Test Track"
        self.description = "Track description"
        self.file_url = "https://example.com/track.mp3"


class FakePlaylistTrack:
    """Mock playlist track object."""
    def __init__(self, playlist_id=None, track_id=None):
        self.playlist_id = playlist_id or uuid.uuid4()
        self.track_id = track_id or uuid.uuid4()


class CreatePlaylistRequest:
    """Mock create playlist request."""
    def __init__(self, name, description=None):
        self.name = name
        self.description = description


class UpdatePlaylistRequest:
    """Mock update playlist request."""
    def __init__(self, name=None, description=None):
        self.name = name
        self.description = description

    def model_dump(self, exclude_unset=False):
        """Mimic pydantic model_dump method."""
        data = {}
        if self.name is not None:
            data["name"] = self.name
        if self.description is not None:
            data["description"] = self.description
        return data


class PlaylistTrackRequest:
    """Mock playlist track request."""
    def __init__(self, track_id):
        self.track_id = track_id


# ────────────────────────────────────────────────────────
# CREATE PLAYLIST TESTS
# ────────────────────────────────────────────────────────

def test_create_playlist_success(monkeypatch):
    """Test successful playlist creation with name and description."""
    db = FakeDB()
    user = FakeUser()
    data = CreatePlaylistRequest(
        name="My Awesome Playlist",
        description="A collection of my favorite songs"
    )

    created_playlists = []

    from app.repositories.playlist_repo import PlaylistRepository

    def fake_create(db_arg, playlist):
        created_playlists.append(playlist)
        if not hasattr(playlist, "playlist_id") or not playlist.playlist_id:
            playlist.playlist_id = uuid.uuid4()

    monkeypatch.setattr(PlaylistRepository, "create", fake_create)

    result = PlaylistService.create_playlist(db, user, data)

    assert result["success"] is True
    assert result["message"] == "Playlist created successfully."
    assert result["data"]["name"] == "My Awesome Playlist"
    assert result["data"]["description"] == "A collection of my favorite songs"
    assert len(created_playlists) == 1
    assert created_playlists[0].user_id == user.user_id


def test_create_playlist_without_description(monkeypatch):
    """Test playlist creation without description (optional field)."""
    db = FakeDB()
    user = FakeUser()
    data = CreatePlaylistRequest(name="Simple Playlist", description=None)

    from app.repositories.playlist_repo import PlaylistRepository

    def fake_create(db_arg, playlist):
        if not hasattr(playlist, "playlist_id") or not playlist.playlist_id:
            playlist.playlist_id = uuid.uuid4()

    monkeypatch.setattr(PlaylistRepository, "create", fake_create)

    result = PlaylistService.create_playlist(db, user, data)

    assert result["success"] is True
    assert result["data"]["name"] == "Simple Playlist"
    assert result["data"]["description"] is None


# ────────────────────────────────────────────────────────
# GET PLAYLIST TESTS
# ────────────────────────────────────────────────────────

def test_get_playlist_success(monkeypatch):
    """Test successful retrieval of an existing playlist."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
        name="My Playlist",
        description="My description"
    )

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: playlist)

    result = PlaylistService.get_playlist(db, playlist_id)

    assert result["success"] is True
    assert result["data"]["playlist_id"] == str(playlist_id)
    assert result["data"]["user_id"] == str(user_id)
    assert result["data"]["name"] == "My Playlist"
    assert result["data"]["description"] == "My description"


def test_get_playlist_not_found(monkeypatch):
    """Test retrieval of non-existent playlist raises 404."""
    db = FakeDB()
    playlist_id = uuid.uuid4()

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: None)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.get_playlist(db, playlist_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Playlist not found"


# ────────────────────────────────────────────────────────
# UPDATE PLAYLIST TESTS
# ────────────────────────────────────────────────────────

def test_update_playlist_success(monkeypatch):
    """Test successful playlist update by the owner."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
        name="Old Name",
        description="Old Description"
    )

    updated_playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
        name="New Name",
        description="New Description"
    )

    data = UpdatePlaylistRequest(name="New Name", description="New Description")

    from app.repositories.playlist_repo import PlaylistRepository

    def fake_get_by_id(db_arg, pid):
        return playlist if pid == playlist_id else None

    def fake_update(db_arg, pl, fields):
        for key, value in fields.items():
            setattr(pl, key, value)
        return pl

    monkeypatch.setattr(PlaylistRepository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(PlaylistRepository, "update", fake_update)

    result = PlaylistService.update_playlist(db, user, playlist_id, data)

    assert result["success"] is True
    assert result["message"] == "Playlist updated successfully."
    assert result["data"]["name"] == "New Name"
    assert result["data"]["description"] == "New Description"


def test_update_playlist_not_found(monkeypatch):
    """Test update of non-existent playlist raises 404."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    user = FakeUser()
    data = UpdatePlaylistRequest(name="New Name")

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: None)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.update_playlist(db, user, playlist_id, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Playlist not found"


def test_update_playlist_unauthorized(monkeypatch):
    """Test update by non-owner raises 403."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    user = FakeUser(user_id=other_user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=owner_id,
        name="Owner's Playlist"
    )

    data = UpdatePlaylistRequest(name="Hacked Name")

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: playlist)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.update_playlist(db, user, playlist_id, data)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You can only update your own playlists"


def test_update_playlist_no_fields_provided(monkeypatch):
    """Test update with no fields to update raises 400."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
    )

    data = UpdatePlaylistRequest(name=None, description=None)

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: playlist)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.update_playlist(db, user, playlist_id, data)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No fields provided for update"


def test_update_playlist_only_name(monkeypatch):
    """Test playlist update with only name field."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
        name="Old Name",
        description="Old Description"
    )

    data = UpdatePlaylistRequest(name="New Name")

    from app.repositories.playlist_repo import PlaylistRepository

    def fake_get_by_id(db_arg, pid):
        return playlist if pid == playlist_id else None

    def fake_update(db_arg, pl, fields):
        for key, value in fields.items():
            setattr(pl, key, value)
        return pl

    monkeypatch.setattr(PlaylistRepository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(PlaylistRepository, "update", fake_update)

    result = PlaylistService.update_playlist(db, user, playlist_id, data)

    assert result["success"] is True
    assert result["data"]["name"] == "New Name"


# ────────────────────────────────────────────────────────
# DELETE PLAYLIST TESTS
# ────────────────────────────────────────────────────────

def test_delete_playlist_success(monkeypatch):
    """Test successful deletion of playlist by owner."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
    )

    from app.repositories.playlist_repo import PlaylistRepository

    def fake_get_by_id(db_arg, pid):
        return playlist if pid == playlist_id else None

    def fake_delete(db_arg, pl):
        pass

    monkeypatch.setattr(PlaylistRepository, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(PlaylistRepository, "delete", fake_delete)

    result = PlaylistService.delete_playlist(db, user, playlist_id)

    assert result["success"] is True
    assert result["message"] == "Playlist deleted successfully."


def test_delete_playlist_not_found(monkeypatch):
    """Test deletion of non-existent playlist raises 404."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    user = FakeUser()

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: None)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.delete_playlist(db, user, playlist_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Playlist not found"


def test_delete_playlist_unauthorized(monkeypatch):
    """Test deletion by non-owner raises 403."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    user = FakeUser(user_id=other_user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=owner_id,
    )

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: playlist)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.delete_playlist(db, user, playlist_id)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You can only delete your own playlists"


# ────────────────────────────────────────────────────────
# ADD TRACK TO PLAYLIST TESTS
# ────────────────────────────────────────────────────────

def test_add_track_to_playlist_success(monkeypatch):
    """Test successfully adding a track to playlist."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
    )

    track = FakeTrack(track_id=track_id)
    data = PlaylistTrackRequest(track_id=str(track_id))

    from app.repositories.playlist_repo import PlaylistRepository
    from app.repositories.track_repo import TrackRepository

    def fake_get_playlist(db_arg, pid):
        return playlist if pid == playlist_id else None

    def fake_get_track(db_arg, tid):
        # Handle both string and UUID comparisons
        tid_str = str(tid)
        return track if tid_str == str(track_id) else None

    def fake_get_playlist_track(db_arg, pid, tid):
        return None

    def fake_add_track(db_arg, pid, tid):
        pass

    monkeypatch.setattr(PlaylistRepository, "get_by_id", fake_get_playlist)
    monkeypatch.setattr(TrackRepository, "get_by_id", fake_get_track)
    monkeypatch.setattr(PlaylistRepository, "get_playlist_track", fake_get_playlist_track)
    monkeypatch.setattr(PlaylistRepository, "add_track", fake_add_track)

    result = PlaylistService.add_track_to_playlist(db, user, playlist_id, data)

    assert result["success"] is True
    assert result["message"] == "Track added to playlist successfully."


def test_add_track_playlist_not_found(monkeypatch):
    """Test adding track to non-existent playlist raises 404."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    user = FakeUser()

    data = PlaylistTrackRequest(track_id=str(track_id))

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: None)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.add_track_to_playlist(db, user, playlist_id, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Playlist not found"


def test_add_track_unauthorized(monkeypatch):
    """Test adding track to playlist by non-owner raises 403."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    user = FakeUser(user_id=other_user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=owner_id,
    )

    data = PlaylistTrackRequest(track_id=str(track_id))

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: playlist)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.add_track_to_playlist(db, user, playlist_id, data)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You can only edit your own playlists"


def test_add_track_track_not_found(monkeypatch):
    """Test adding non-existent track to playlist raises 404."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    nonexistent_track_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
    )

    data = PlaylistTrackRequest(track_id=str(nonexistent_track_id))

    from app.repositories.playlist_repo import PlaylistRepository
    from app.repositories.track_repo import TrackRepository

    def fake_get_playlist(db_arg, pid):
        return playlist if pid == playlist_id else None

    def fake_get_track(db_arg, tid):
        # This will return None for any track_id lookup
        return None

    monkeypatch.setattr(PlaylistRepository, "get_by_id", fake_get_playlist)
    monkeypatch.setattr(TrackRepository, "get_by_id", fake_get_track)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.add_track_to_playlist(db, user, playlist_id, data)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Track not found"


def test_add_track_duplicate_track(monkeypatch):
    """Test adding duplicate track to playlist raises 409."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
    )

    track = FakeTrack(track_id=track_id)
    existing_playlist_track = FakePlaylistTrack(playlist_id=playlist_id, track_id=track_id)
    data = PlaylistTrackRequest(track_id=str(track_id))

    from app.repositories.playlist_repo import PlaylistRepository
    from app.repositories.track_repo import TrackRepository

    def fake_get_playlist(db_arg, pid):
        return playlist if pid == playlist_id else None

    def fake_get_track(db_arg, tid):
        # Handle both string and UUID comparisons
        tid_str = str(tid)
        return track if tid_str == str(track_id) else None

    def fake_get_playlist_track(db_arg, pid, tid):
        # Handle both string and UUID comparisons
        tid_str = str(tid)
        return existing_playlist_track if (pid == playlist_id and tid_str == str(track_id)) else None

    monkeypatch.setattr(PlaylistRepository, "get_by_id", fake_get_playlist)
    monkeypatch.setattr(TrackRepository, "get_by_id", fake_get_track)
    monkeypatch.setattr(PlaylistRepository, "get_playlist_track", fake_get_playlist_track)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.add_track_to_playlist(db, user, playlist_id, data)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Track already exists in playlist"


# ────────────────────────────────────────────────────────
# REMOVE TRACK FROM PLAYLIST TESTS
# ────────────────────────────────────────────────────────

def test_remove_track_from_playlist_success(monkeypatch):
    """Test successfully removing a track from playlist."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
    )

    playlist_track = FakePlaylistTrack(playlist_id=playlist_id, track_id=track_id)

    from app.repositories.playlist_repo import PlaylistRepository

    def fake_get_playlist(db_arg, pid):
        return playlist if pid == playlist_id else None

    def fake_get_playlist_track(db_arg, pid, tid):
        return playlist_track if (pid == playlist_id and tid == track_id) else None

    def fake_remove_track(db_arg, pt):
        pass

    monkeypatch.setattr(PlaylistRepository, "get_by_id", fake_get_playlist)
    monkeypatch.setattr(PlaylistRepository, "get_playlist_track", fake_get_playlist_track)
    monkeypatch.setattr(PlaylistRepository, "remove_track", fake_remove_track)

    result = PlaylistService.remove_track_from_playlist(db, user, playlist_id, track_id)

    assert result["success"] is True
    assert result["message"] == "Track removed from playlist successfully."


def test_remove_track_playlist_not_found(monkeypatch):
    """Test removing track from non-existent playlist raises 404."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    user = FakeUser()

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: None)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.remove_track_from_playlist(db, user, playlist_id, track_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Playlist not found"


def test_remove_track_unauthorized(monkeypatch):
    """Test removing track from playlist by non-owner raises 403."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    user = FakeUser(user_id=other_user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=owner_id,
    )

    from app.repositories.playlist_repo import PlaylistRepository
    monkeypatch.setattr(PlaylistRepository, "get_by_id", lambda db_arg, pid: playlist)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.remove_track_from_playlist(db, user, playlist_id, track_id)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You can only edit your own playlists"


def test_remove_track_not_in_playlist(monkeypatch):
    """Test removing non-existent track from playlist raises 404."""
    db = FakeDB()
    playlist_id = uuid.uuid4()
    track_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = FakeUser(user_id=user_id)

    playlist = FakePlaylist(
        playlist_id=playlist_id,
        user_id=user_id,
    )

    from app.repositories.playlist_repo import PlaylistRepository

    def fake_get_playlist(db_arg, pid):
        return playlist if pid == playlist_id else None

    monkeypatch.setattr(PlaylistRepository, "get_by_id", fake_get_playlist)
    monkeypatch.setattr(PlaylistRepository, "get_playlist_track", lambda db_arg, pid, tid: None)

    with pytest.raises(HTTPException) as exc_info:
        PlaylistService.remove_track_from_playlist(db, user, playlist_id, track_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Track not found in playlist"

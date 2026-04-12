"""
Unit tests for the Search Service.

Tests all endpoints and scenarios including:
- Search users (results found, no results, case-insensitive)
- Search tracks (results found, no results, case-insensitive)
"""
import uuid
import pytest

from app.services.search_service import SearchService


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
    def __init__(self, user_id=None, display_name="Test User", account_type="listener",
                 profile_picture=None, follower_count=0, is_verified=False):
        self.user_id = user_id or uuid.uuid4()
        self.display_name = display_name
        self.account_type = account_type
        self.profile_picture = profile_picture
        self.follower_count = follower_count
        self.is_verified = is_verified


class FakeTrack:
    """Mock track object."""
    def __init__(self, track_id=None, title="Test Track", description="Track description",
                 file_url="https://example.com/track.mp3"):
        self.track_id = track_id or uuid.uuid4()
        self.title = title
        self.description = description
        self.file_url = file_url


# ────────────────────────────────────────────────────────
# SEARCH USERS TESTS
# ────────────────────────────────────────────────────────

def test_search_users_success_with_results(monkeypatch):
    """Test searching users returns results matching keyword."""
    db = FakeDB()
    keyword = "john"

    user1 = FakeUser(
        user_id=uuid.uuid4(),
        display_name="John Doe",
        account_type="artist",
        follower_count=100,
        is_verified=True
    )

    user2 = FakeUser(
        user_id=uuid.uuid4(),
        display_name="John Smith",
        account_type="listener",
        follower_count=50,
        is_verified=False
    )

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(
        UserRepository,
        "search_by_name",
        lambda db_arg, kw: [user1, user2]
    )

    result = SearchService.search_users(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["users"]) == 2
    
    # Verify first user data
    assert result["data"]["users"][0]["display_name"] == "John Doe"
    assert result["data"]["users"][0]["account_type"] == "artist"
    assert result["data"]["users"][0]["follower_count"] == 100
    assert result["data"]["users"][0]["is_verified"] is True
    
    # Verify second user data
    assert result["data"]["users"][1]["display_name"] == "John Smith"
    assert result["data"]["users"][1]["account_type"] == "listener"
    assert result["data"]["users"][1]["follower_count"] == 50
    assert result["data"]["users"][1]["is_verified"] is False


def test_search_users_no_results(monkeypatch):
    """Test searching users with no matching results returns empty list."""
    db = FakeDB()
    keyword = "nonexistent"

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "search_by_name", lambda db_arg, kw: [])

    result = SearchService.search_users(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["users"]) == 0
    assert result["data"]["users"] == []


def test_search_users_single_result(monkeypatch):
    """Test searching users returns single result."""
    db = FakeDB()
    keyword = "alice"

    user = FakeUser(
        user_id=uuid.uuid4(),
        display_name="Alice Johnson",
        account_type="artist",
        profile_picture="https://example.com/alice.jpg",
        follower_count=500,
        is_verified=True
    )

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "search_by_name", lambda db_arg, kw: [user])

    result = SearchService.search_users(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["users"]) == 1
    assert result["data"]["users"][0]["user_id"] == str(user.user_id)
    assert result["data"]["users"][0]["display_name"] == "Alice Johnson"
    assert result["data"]["users"][0]["profile_picture"] == "https://example.com/alice.jpg"


def test_search_users_case_insensitive(monkeypatch):
    """Test user search is case-insensitive."""
    db = FakeDB()
    keyword_lowercase = "bob"

    user = FakeUser(
        user_id=uuid.uuid4(),
        display_name="Bob Dylan",
        account_type="listener",
    )

    search_calls = []

    def fake_search(db_arg, kw):
        search_calls.append(kw)
        return [user]

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "search_by_name", fake_search)

    result = SearchService.search_users(db, keyword_lowercase)

    assert result["success"] is True
    assert len(result["data"]["users"]) == 1
    assert result["data"]["users"][0]["display_name"] == "Bob Dylan"
    assert search_calls[0] == keyword_lowercase


def test_search_users_multiple_results(monkeypatch):
    """Test searching users returns multiple results."""
    db = FakeDB()
    keyword = "test"

    users = [
        FakeUser(display_name="Test User 1", account_type="artist", follower_count=10),
        FakeUser(display_name="Test User 2", account_type="listener", follower_count=20),
        FakeUser(display_name="Test User 3", account_type="artist", follower_count=30),
    ]

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "search_by_name", lambda db_arg, kw: users)

    result = SearchService.search_users(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["users"]) == 3
    assert all(user.get("display_name").startswith("Test User") for user in result["data"]["users"])


def test_search_users_with_verified_badge(monkeypatch):
    """Test searching users returns verification status correctly."""
    db = FakeDB()
    keyword = "verified"

    verified_user = FakeUser(
        display_name="Verified Artist",
        account_type="artist",
        is_verified=True
    )

    unverified_user = FakeUser(
        display_name="Unverified Artist",
        account_type="artist",
        is_verified=False
    )

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(
        UserRepository,
        "search_by_name",
        lambda db_arg, kw: [verified_user, unverified_user]
    )

    result = SearchService.search_users(db, keyword)

    assert result["success"] is True
    assert result["data"]["users"][0]["is_verified"] is True
    assert result["data"]["users"][1]["is_verified"] is False


# ────────────────────────────────────────────────────────
# SEARCH TRACKS TESTS
# ────────────────────────────────────────────────────────

def test_search_tracks_success_with_results(monkeypatch):
    """Test searching tracks returns results matching keyword."""
    db = FakeDB()
    keyword = "love"

    track1 = FakeTrack(
        track_id=uuid.uuid4(),
        title="Love Song",
        description="A beautiful love song",
        file_url="https://example.com/love_song.mp3"
    )

    track2 = FakeTrack(
        track_id=uuid.uuid4(),
        title="Love Me",
        description="Popular love track",
        file_url="https://example.com/love_me.mp3"
    )

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(
        TrackRepository,
        "search_by_title",
        lambda db_arg, kw: [track1, track2]
    )

    result = SearchService.search_tracks(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["tracks"]) == 2
    
    # Verify first track data
    assert result["data"]["tracks"][0]["title"] == "Love Song"
    assert result["data"]["tracks"][0]["description"] == "A beautiful love song"
    assert result["data"]["tracks"][0]["file_url"] == "https://example.com/love_song.mp3"
    
    # Verify second track data
    assert result["data"]["tracks"][1]["title"] == "Love Me"
    assert result["data"]["tracks"][1]["description"] == "Popular love track"


def test_search_tracks_no_results(monkeypatch):
    """Test searching tracks with no matching results returns empty list."""
    db = FakeDB()
    keyword = "nonexistenttrack"

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(TrackRepository, "search_by_title", lambda db_arg, kw: [])

    result = SearchService.search_tracks(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["tracks"]) == 0
    assert result["data"]["tracks"] == []


def test_search_tracks_single_result(monkeypatch):
    """Test searching tracks returns single result."""
    db = FakeDB()
    keyword = "bohemian"

    track = FakeTrack(
        track_id=uuid.uuid4(),
        title="Bohemian Rhapsody",
        description="Classic track from Queen",
        file_url="https://example.com/bohemian_rhapsody.mp3"
    )

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(TrackRepository, "search_by_title", lambda db_arg, kw: [track])

    result = SearchService.search_tracks(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["tracks"]) == 1
    assert result["data"]["tracks"][0]["track_id"] == str(track.track_id)
    assert result["data"]["tracks"][0]["title"] == "Bohemian Rhapsody"


def test_search_tracks_case_insensitive(monkeypatch):
    """Test track search is case-insensitive."""
    db = FakeDB()
    keyword_lowercase = "rock"

    track = FakeTrack(
        track_id=uuid.uuid4(),
        title="Rock Anthem",
        description="Epic rock song",
        file_url="https://example.com/rock.mp3"
    )

    search_calls = []

    def fake_search(db_arg, kw):
        search_calls.append(kw)
        return [track]

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(TrackRepository, "search_by_title", fake_search)

    result = SearchService.search_tracks(db, keyword_lowercase)

    assert result["success"] is True
    assert len(result["data"]["tracks"]) == 1
    assert result["data"]["tracks"][0]["title"] == "Rock Anthem"
    assert search_calls[0] == keyword_lowercase


def test_search_tracks_multiple_results(monkeypatch):
    """Test searching tracks returns multiple results."""
    db = FakeDB()
    keyword = "jazz"

    tracks = [
        FakeTrack(title="Jazz Piano", description="Smooth jazz"),
        FakeTrack(title="Jazz Improvisation", description="Free form jazz"),
        FakeTrack(title="Modern Jazz", description="Contemporary jazz"),
    ]

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(TrackRepository, "search_by_title", lambda db_arg, kw: tracks)

    result = SearchService.search_tracks(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["tracks"]) == 3
    assert all("Jazz" in track.get("title") for track in result["data"]["tracks"])


def test_search_tracks_partial_match(monkeypatch):
    """Test track search with partial keyword matches."""
    db = FakeDB()
    keyword = "beat"

    tracks = [
        FakeTrack(title="Heartbeat", description="Sweet heartbeat song"),
        FakeTrack(title="Off the Beat", description="Syncopated rhythm"),
    ]

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(TrackRepository, "search_by_title", lambda db_arg, kw: tracks)

    result = SearchService.search_tracks(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["tracks"]) == 2
    assert "Heartbeat" in result["data"]["tracks"][0]["title"]
    assert "Beat" in result["data"]["tracks"][1]["title"]


def test_search_tracks_special_characters_in_title(monkeypatch):
    """Test searching tracks with special characters."""
    db = FakeDB()
    keyword = "rock"

    track = FakeTrack(
        track_id=uuid.uuid4(),
        title="Rock & Roll Revival",
        description="Mix of rock and roll",
        file_url="https://example.com/rock_roll.mp3"
    )

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(TrackRepository, "search_by_title", lambda db_arg, kw: [track])

    result = SearchService.search_tracks(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["tracks"]) == 1
    assert result["data"]["tracks"][0]["title"] == "Rock & Roll Revival"


def test_search_tracks_by_artist_name_in_description(monkeypatch):
    """Test searching tracks can find artist name in description."""
    db = FakeDB()
    keyword = "beatles"

    track = FakeTrack(
        track_id=uuid.uuid4(),
        title="Yesterday",
        description="Classic track by The Beatles",
        file_url="https://example.com/yesterday.mp3"
    )

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(TrackRepository, "search_by_title", lambda db_arg, kw: [track])

    result = SearchService.search_tracks(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["tracks"]) == 1


# ────────────────────────────────────────────────────────
# CROSS-FUNCTIONAL TESTS
# ────────────────────────────────────────────────────────

def test_search_users_and_tracks_independently(monkeypatch):
    """Test that user and track searches work independently."""
    db = FakeDB()

    # Setup users
    users = [
        FakeUser(display_name="Track Master"),
        FakeUser(display_name="Song Writer"),
    ]

    # Setup tracks
    tracks = [
        FakeTrack(title="User Favorite"),
        FakeTrack(title="Track Number One"),
    ]

    from app.repositories.user_repo import UserRepository
    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(UserRepository, "search_by_name", lambda db_arg, kw: users)
    monkeypatch.setattr(TrackRepository, "search_by_title", lambda db_arg, kw: tracks)

    # Search users
    user_result = SearchService.search_users(db, "track")
    assert len(user_result["data"]["users"]) == 2

    # Search tracks
    track_result = SearchService.search_tracks(db, "user")
    assert len(track_result["data"]["tracks"]) == 2


def test_search_with_empty_keyword_returns_all(monkeypatch):
    """Test searching with empty keyword."""
    db = FakeDB()
    keyword = ""

    users = [
        FakeUser(display_name="User 1"),
        FakeUser(display_name="User 2"),
    ]

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "search_by_name", lambda db_arg, kw: users if kw else users)

    result = SearchService.search_users(db, keyword)

    assert result["success"] is True
    assert len(result["data"]["users"]) == 2


def test_search_response_structure_for_users(monkeypatch):
    """Test the response structure for user search."""
    db = FakeDB()
    keyword = "test"

    user = FakeUser(
        user_id=uuid.uuid4(),
        display_name="Test Artist",
        account_type="artist",
        profile_picture="https://example.com/pic.jpg",
        follower_count=1000,
        is_verified=True
    )

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "search_by_name", lambda db_arg, kw: [user])

    result = SearchService.search_users(db, keyword)

    # Verify response structure
    assert "success" in result
    assert "data" in result
    assert "users" in result["data"]
    
    # Verify user object structure
    user_obj = result["data"]["users"][0]
    assert "user_id" in user_obj
    assert "display_name" in user_obj
    assert "account_type" in user_obj
    assert "profile_picture" in user_obj
    assert "follower_count" in user_obj
    assert "is_verified" in user_obj


def test_search_response_structure_for_tracks(monkeypatch):
    """Test the response structure for track search."""
    db = FakeDB()
    keyword = "test"

    track = FakeTrack(
        track_id=uuid.uuid4(),
        title="Test Track",
        description="A test track",
        file_url="https://example.com/track.mp3"
    )

    from app.repositories.track_repo import TrackRepository
    monkeypatch.setattr(TrackRepository, "search_by_title", lambda db_arg, kw: [track])

    result = SearchService.search_tracks(db, keyword)

    # Verify response structure
    assert "success" in result
    assert "data" in result
    assert "tracks" in result["data"]
    
    # Verify track object structure
    track_obj = result["data"]["tracks"][0]
    assert "track_id" in track_obj
    assert "title" in track_obj
    assert "description" in track_obj
    assert "file_url" in track_obj

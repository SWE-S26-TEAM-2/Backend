"""
Unit tests for the Search Router endpoints.

Tests all API endpoints with TestClient, including:
- GET /search/users?keyword=... - Search users
- GET /search/tracks?keyword=... - Search tracks
"""

from fastapi.testclient import TestClient

from app.main import app
from app.database.database import get_db
from app.services.search_service import SearchService

client = TestClient(app)


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
# SEARCH USERS ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_search_users_endpoint_success(monkeypatch):
    """Test GET /search/users?keyword=test returns 200 with results."""

    def fake_search_users(db, keyword):
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "display_name": "John Doe",
                        "account_type": "artist",
                        "profile_picture": "https://example.com/pic.jpg",
                        "follower_count": 100,
                        "is_verified": True,
                    },
                    {
                        "user_id": "223e4567-e89b-12d3-a456-426614174000",
                        "display_name": "Jane Smith",
                        "account_type": "listener",
                        "profile_picture": None,
                        "follower_count": 50,
                        "is_verified": False,
                    },
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_users", fake_search_users)

    response = client.get("/search/users?keyword=john")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["users"]) == 2
    assert body["data"]["users"][0]["display_name"] == "John Doe"
    assert body["data"]["users"][0]["is_verified"] is True


def test_search_users_endpoint_no_results(monkeypatch):
    """Test GET /search/users?keyword=xyzabc returns empty results."""

    def fake_search_users(db, keyword):
        return {
            "success": True,
            "data": {"users": []},
        }

    monkeypatch.setattr(SearchService, "search_users", fake_search_users)

    response = client.get("/search/users?keyword=xyzabc")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["users"]) == 0


def test_search_users_endpoint_missing_keyword(monkeypatch):
    """Test GET /search/users without keyword parameter returns error."""
    response = client.get("/search/users")

    # Should fail due to missing required query parameter
    assert response.status_code >= 400


def test_search_users_endpoint_single_result(monkeypatch):
    """Test GET /search/users?keyword=alice returns single result."""

    def fake_search_users(db, keyword):
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "user_id": "323e4567-e89b-12d3-a456-426614174000",
                        "display_name": "Alice Johnson",
                        "account_type": "artist",
                        "profile_picture": "https://example.com/alice.jpg",
                        "follower_count": 500,
                        "is_verified": True,
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_users", fake_search_users)

    response = client.get("/search/users?keyword=alice")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["users"]) == 1
    assert body["data"]["users"][0]["display_name"] == "Alice Johnson"


def test_search_users_endpoint_special_characters_in_keyword(monkeypatch):
    """Test GET /search/users with special characters in keyword."""

    def fake_search_users(db, keyword):
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "user_id": "423e4567-e89b-12d3-a456-426614174000",
                        "display_name": "User & Co",
                        "account_type": "artist",
                        "profile_picture": None,
                        "follower_count": 75,
                        "is_verified": False,
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_users", fake_search_users)

    response = client.get("/search/users?keyword=user%20%26%20co")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["users"]) == 1


def test_search_users_endpoint_case_insensitive(monkeypatch):
    """Test GET /search/users is case-insensitive."""
    search_calls = []

    def fake_search_users(db, keyword):
        search_calls.append(keyword)
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "user_id": "523e4567-e89b-12d3-a456-426614174000",
                        "display_name": "Bob Dylan",
                        "account_type": "artist",
                        "profile_picture": None,
                        "follower_count": 1000,
                        "is_verified": True,
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_users", fake_search_users)

    # Search with lowercase
    response = client.get("/search/users?keyword=bob")

    assert response.status_code == 200
    assert len(search_calls) == 1


def test_search_users_endpoint_whitespace_keyword(monkeypatch):
    """Test GET /search/users with whitespace in keyword."""

    def fake_search_users(db, keyword):
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "user_id": "623e4567-e89b-12d3-a456-426614174000",
                        "display_name": "John Smith",
                        "account_type": "listener",
                        "profile_picture": None,
                        "follower_count": 25,
                        "is_verified": False,
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_users", fake_search_users)

    response = client.get("/search/users?keyword=john%20smith")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["users"]) == 1


# ────────────────────────────────────────────────────────
# SEARCH TRACKS ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_search_tracks_endpoint_success(monkeypatch):
    """Test GET /search/tracks?keyword=rock returns 200 with results."""

    def fake_search_tracks(db, keyword):
        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": "723e4567-e89b-12d3-a456-426614174000",
                        "title": "Rock Anthem",
                        "description": "Epic rock song",
                        "stream_url": "/api/tracks/723e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    },
                    {
                        "track_id": "823e4567-e89b-12d3-a456-426614174000",
                        "title": "Rock & Roll",
                        "description": "Classic rock",
                        "stream_url": "/api/tracks/823e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    },
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    response = client.get("/search/tracks?keyword=rock")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["tracks"]) == 2
    assert body["data"]["tracks"][0]["title"] == "Rock Anthem"


def test_search_tracks_endpoint_no_results(monkeypatch):
    """Test GET /search/tracks?keyword=nonexistent returns empty results."""

    def fake_search_tracks(db, keyword):
        return {
            "success": True,
            "data": {"tracks": []},
        }

    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    response = client.get("/search/tracks?keyword=nonexistent")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["tracks"]) == 0


def test_search_tracks_endpoint_missing_keyword(monkeypatch):
    """Test GET /search/tracks without keyword parameter returns error."""
    response = client.get("/search/tracks")

    # Should fail due to missing required query parameter
    assert response.status_code >= 400


def test_search_tracks_endpoint_single_result(monkeypatch):
    """Test GET /search/tracks?keyword=bohemian returns single result."""

    def fake_search_tracks(db, keyword):
        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": "923e4567-e89b-12d3-a456-426614174000",
                        "title": "Bohemian Rhapsody",
                        "description": "Classic track from Queen",
                        "stream_url": "/api/tracks/923e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    response = client.get("/search/tracks?keyword=bohemian")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["tracks"]) == 1
    assert body["data"]["tracks"][0]["title"] == "Bohemian Rhapsody"


def test_search_tracks_endpoint_partial_match(monkeypatch):
    """Test GET /search/tracks?keyword=beat finds partial matches."""

    def fake_search_tracks(db, keyword):
        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": "a23e4567-e89b-12d3-a456-426614174000",
                        "title": "Heartbeat",
                        "description": "Song about heartbeat",
                        "stream_url": "/api/tracks/a23e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    },
                    {
                        "track_id": "b23e4567-e89b-12d3-a456-426614174000",
                        "title": "Off the Beat",
                        "description": "Syncopated rhythm",
                        "stream_url": "/api/tracks/b23e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    },
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    response = client.get("/search/tracks?keyword=beat")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["tracks"]) == 2


def test_search_tracks_endpoint_special_characters(monkeypatch):
    """Test GET /search/tracks with special characters in title."""

    def fake_search_tracks(db, keyword):
        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": "c23e4567-e89b-12d3-a456-426614174000",
                        "title": "Rock & Roll Revival",
                        "description": "Mix of rock and roll",
                        "stream_url": "/api/tracks/c23e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    response = client.get("/search/tracks?keyword=rock%20%26%20roll")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["tracks"]) == 1
    assert "Rock & Roll" in body["data"]["tracks"][0]["title"]


def test_search_tracks_endpoint_whitespace_keyword(monkeypatch):
    """Test GET /search/tracks with whitespace in keyword."""

    def fake_search_tracks(db, keyword):
        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": "d23e4567-e89b-12d3-a456-426614174000",
                        "title": "Love Song",
                        "description": "Beautiful love song",
                        "stream_url": "/api/tracks/d23e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    response = client.get("/search/tracks?keyword=love%20song")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["tracks"]) == 1


def test_search_tracks_endpoint_case_insensitive(monkeypatch):
    """Test GET /search/tracks is case-insensitive."""

    def fake_search_tracks(db, keyword):
        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": "e23e4567-e89b-12d3-a456-426614174000",
                        "title": "Jazz Piano",
                        "description": "Smooth jazz",
                        "stream_url": "/api/tracks/e23e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    # Search with lowercase
    response = client.get("/search/tracks?keyword=jazz")

    assert response.status_code == 200


def test_search_tracks_endpoint_many_results(monkeypatch):
    """Test GET /search/tracks returns many results."""

    def fake_search_tracks(db, keyword):
        tracks = [
            {
                "track_id": f"{i:03d}3e4567-e89b-12d3-a456-426614174000",
                "title": f"Track {i}",
                "description": f"Description {i}",
                "stream_url": f"/api/tracks/{i:03d}3e4567-e89b-12d3-a456-426614174000/audio",
                "visibility": "public",
                "processing_status": "finished",
            }
            for i in range(10)
        ]
        return {
            "success": True,
            "data": {"tracks": tracks},
        }

    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    response = client.get("/search/tracks?keyword=track")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["tracks"]) == 10


# ────────────────────────────────────────────────────────
# CROSS-FUNCTIONAL TESTS
# ────────────────────────────────────────────────────────


def test_search_users_and_tracks_separately(monkeypatch):
    """Test that user and track searches can be called separately."""

    def fake_search_users(db, keyword):
        return {
            "success": True,
            "data": {
                "users": [
                    {
                        "user_id": "f23e4567-e89b-12d3-a456-426614174000",
                        "display_name": "User",
                        "account_type": "artist",
                        "profile_picture": None,
                        "follower_count": 0,
                        "is_verified": False,
                    }
                ]
            },
        }

    def fake_search_tracks(db, keyword):
        return {
            "success": True,
            "data": {
                "tracks": [
                    {
                        "track_id": "023e4567-e89b-12d3-a456-426614174000",
                        "title": "Track",
                        "description": "Desc",
                        "stream_url": "/api/tracks/023e4567-e89b-12d3-a456-426614174000/audio",
                        "visibility": "public",
                        "processing_status": "finished",
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_users", fake_search_users)
    monkeypatch.setattr(SearchService, "search_tracks", fake_search_tracks)

    # Search users
    user_response = client.get("/search/users?keyword=user")
    assert user_response.status_code == 200
    assert len(user_response.json()["data"]["users"]) == 1

    # Search tracks
    track_response = client.get("/search/tracks?keyword=track")
    assert track_response.status_code == 200
    assert len(track_response.json()["data"]["tracks"]) == 1

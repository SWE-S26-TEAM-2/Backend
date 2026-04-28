"""
Unit tests for the User Profile Router endpoints.

Tests all API endpoints with TestClient, including:
- GET /users/me - Get own profile
- GET /users/{user_id} - Get any user's profile
- PATCH /users/me - Update profile
- PATCH /users/me/privacy - Update privacy
- PUT /users/me/avatar - Upload avatar
- PUT /users/me/cover - Upload cover photo
- GET /users/me/social-links - Get social links
- PUT /users/me/social-links - Update social links
"""

import uuid
import io
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user, get_optional_current_user
from app.database.database import get_db
from app.services.user_service import UserService
from app.services.social_link_service import SocialLinkService
from app.services.track_service import TrackService

client = TestClient(app)


class FakeUser:
    """Mock user for dependency override."""

    def __init__(
        self,
        user_id=None,
        email="test@example.com",
        display_name="Test User",
        is_private=False,
        profile_picture=None,
        cover_photo=None,
    ):
        self.user_id = user_id or uuid.uuid4()
        self.email = email
        self.username = "testuser"
        self.display_name = display_name
        self.account_type = "listener"
        self.is_verified = True
        self.is_suspended = False
        self.bio = "Test bio"
        self.location = "Test City"
        self.is_premium = False
        self.is_private = is_private
        self.profile_picture = profile_picture
        self.cover_photo = cover_photo
        self.follower_count = 0
        self.following_count = 0
        self.track_count = 0
        self.created_at = "2024-01-01T00:00:00Z"
        self.updated_at = None


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
# GET MY PROFILE ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_get_my_profile_endpoint_success(monkeypatch):
    """Test GET /users/me returns 200 with full profile."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_get_profile(user):
        return {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "email": "user@example.com",
                "username": "testuser",
                "display_name": "Test User",
                "account_type": "listener",
                "is_verified": True,
                "is_suspended": False,
                "is_premium": False,
                "is_private": False,
                "follower_count": 0,
                "following_count": 0,
                "track_count": 0,
            },
        }

    monkeypatch.setattr(UserService, "get_my_profile", fake_get_profile)

    response = client.get("/users/me")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["display_name"] == "Test User"


def test_get_my_profile_endpoint_without_auth(monkeypatch):
    """Test GET /users/me without authentication returns 401."""
    app.dependency_overrides.pop(get_current_user, None)

    response = client.get("/users/me")

    assert response.status_code == 401

    app.dependency_overrides[get_current_user] = lambda: FakeUser()


# ────────────────────────────────────────────────────────
# GET USER PROFILE BY ID ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_get_user_profile_endpoint_success(monkeypatch):
    """Test GET /users/{username} returns 200 with public profile."""
    user_id = uuid.uuid4()

    def fake_get_profile(db, username):
        return {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "username": username,
                "display_name": "Public User",
                "account_type": "artist",
                "bio": "Artist bio",
                "follower_count": 100,
            },
        }

    monkeypatch.setattr(UserService, "get_profile_by_username", fake_get_profile)

    response = client.get("/users/publicuser")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["display_name"] == "Public User"


def test_get_user_profile_endpoint_private(monkeypatch):
    """Test GET /users/{username} returns limited data for private profile."""
    user_id = uuid.uuid4()

    def fake_get_profile(db, username):
        return {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "username": username,
                "display_name": "Private User",
                "profile_picture": None,
                "follower_count": 50,
            },
        }

    monkeypatch.setattr(UserService, "get_profile_by_username", fake_get_profile)

    response = client.get("/users/privateuser")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["display_name"] == "Private User"
    assert body["data"]["following_count"] is None
    assert body["data"]["track_count"] is None


def test_get_user_profile_endpoint_not_found(monkeypatch):
    """Test GET /users/{username} returns 404 for non-existent user."""
    from fastapi import HTTPException, status

    def fake_get_profile(db, username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    monkeypatch.setattr(UserService, "get_profile_by_username", fake_get_profile)

    response = client.get("/users/nobody")

    assert response.status_code == 404


def test_get_user_profile_endpoint_invalid_id(monkeypatch):
    """Test GET /users/me still works (not treated as username)."""
    app.dependency_overrides[get_current_user] = lambda: FakeUser()

    def fake_get_profile(user):
        return {
            "success": True,
            "data": {
                "user_id": str(uuid.uuid4()),
                "email": "test@example.com",
                "username": "testuser",
                "display_name": "Test User",
                "account_type": "listener",
                "is_verified": True,
                "is_suspended": False,
                "is_premium": False,
                "is_private": False,
                "follower_count": 0,
                "following_count": 0,
                "track_count": 0,
            },
        }

    monkeypatch.setattr(UserService, "get_my_profile", fake_get_profile)

    response = client.get("/users/me")

    assert response.status_code == 200


def test_get_user_tracks_endpoint_success(monkeypatch):
    """Test GET /users/{username}/tracks returns a track list."""
    user_id = uuid.uuid4()
    track_id = uuid.uuid4()
    fake_user = FakeUser(user_id=user_id)

    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_username", lambda db, u: fake_user)
    monkeypatch.setattr(
        TrackService,
        "get_tracks_by_user",
        lambda db, uid, current_user=None: {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "tracks": [
                    {
                        "track_id": str(track_id),
                        "title": "Profile Track",
                        "description": "From user profile",
                        "stream_url": f"/api/tracks/{track_id}/audio",
                        "user_id": str(user_id),
                        "visibility": "public",
                        "processing_status": "finished",
                        "play_count": 0,
                    }
                ],
            },
        },
    )

    response = client.get("/users/testuser/tracks")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["tracks"][0]["title"] == "Profile Track"


def test_get_user_tracks_endpoint_passes_authenticated_user(monkeypatch):
    """Test GET /users/{username}/tracks forwards optional auth context."""
    user_id = uuid.uuid4()
    seen_user_ids = []
    fake_user = FakeUser(user_id=user_id)

    app.dependency_overrides[get_optional_current_user] = lambda: fake_user

    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_username", lambda db, u: fake_user)

    def fake_get_tracks(db, uid, current_user=None):
        seen_user_ids.append(current_user.user_id if current_user else None)
        return {"success": True, "data": {"user_id": str(uid), "tracks": []}}

    monkeypatch.setattr(TrackService, "get_tracks_by_user", fake_get_tracks)

    response = client.get("/users/testuser/tracks")

    assert response.status_code == 200
    assert seen_user_ids == [user_id]

    app.dependency_overrides.pop(get_optional_current_user, None)


def test_get_user_tracks_endpoint_not_found(monkeypatch):
    """Test GET /users/{username}/tracks returns 404 for missing user."""
    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_username", lambda db, u: None)

    response = client.get("/users/nobody/tracks")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_liked_tracks_endpoint_success(monkeypatch):
    """Test GET /users/{username}/liked-tracks returns a track list."""
    user_id = uuid.uuid4()
    track_id = uuid.uuid4()
    fake_user = FakeUser(user_id=user_id)

    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_username", lambda db, u: fake_user)
    monkeypatch.setattr(
        TrackService,
        "get_liked_tracks_by_user",
        lambda db, uid, current_user=None: {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "tracks": [
                    {
                        "track_id": str(track_id),
                        "title": "Liked Track",
                        "description": "From likes",
                        "stream_url": f"/api/tracks/{track_id}/audio",
                        "user_id": str(user_id),
                        "visibility": "public",
                        "processing_status": "finished",
                        "play_count": 0,
                    }
                ],
            },
        },
    )

    response = client.get("/users/testuser/liked-tracks")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["tracks"][0]["title"] == "Liked Track"


def test_get_user_liked_tracks_endpoint_passes_authenticated_user(monkeypatch):
    """Test GET /users/{username}/liked-tracks forwards optional auth context."""
    user_id = uuid.uuid4()
    seen_user_ids = []
    fake_user = FakeUser(user_id=user_id)

    app.dependency_overrides[get_optional_current_user] = lambda: fake_user

    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_username", lambda db, u: fake_user)

    def fake_get_liked_tracks(db, uid, current_user=None):
        seen_user_ids.append(current_user.user_id if current_user else None)
        return {"success": True, "data": {"user_id": str(uid), "tracks": []}}

    monkeypatch.setattr(TrackService, "get_liked_tracks_by_user", fake_get_liked_tracks)

    response = client.get("/users/testuser/liked-tracks")

    assert response.status_code == 200
    assert seen_user_ids == [user_id]

    app.dependency_overrides.pop(get_optional_current_user, None)


def test_get_user_liked_tracks_endpoint_not_found(monkeypatch):
    """Test GET /users/{username}/liked-tracks returns 404 for missing user."""
    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(UserRepository, "get_by_username", lambda db, u: None)

    response = client.get("/users/nobody/liked-tracks")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


# ────────────────────────────────────────────────────────
# UPDATE PROFILE ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_update_profile_endpoint_success(monkeypatch):
    """Test PATCH /users/me returns 200 with updated profile."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_update(db, user, data):
        return {
            "success": True,
            "message": "Profile updated successfully.",
            "data": {
                "user_id": str(user_id),
                "username": "testuser",
                "display_name": "Updated Name",
                "bio": "Updated bio",
                "account_type": "listener",
            },
        }

    monkeypatch.setattr(UserService, "update_profile", fake_update)

    response = client.patch(
        "/users/me", json={"display_name": "Updated Name", "bio": "Updated bio"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["display_name"] == "Updated Name"


def test_update_profile_endpoint_partial(monkeypatch):
    """Test PATCH /users/me updating only some fields."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_update(db, user, data):
        return {
            "success": True,
            "message": "Profile updated successfully.",
            "data": {
                "user_id": str(user_id),
                "username": "testuser",
                "display_name": "New Name",
                "account_type": "listener",
            },
        }

    monkeypatch.setattr(UserService, "update_profile", fake_update)

    response = client.patch("/users/me", json={"display_name": "New Name"})

    assert response.status_code == 200


def test_update_profile_endpoint_without_auth(monkeypatch):
    """Test PATCH /users/me without authentication returns 401."""
    app.dependency_overrides.pop(get_current_user, None)

    response = client.patch("/users/me", json={"display_name": "Hacker"})

    assert response.status_code == 401

    app.dependency_overrides[get_current_user] = lambda: FakeUser()


# ────────────────────────────────────────────────────────
# UPDATE PRIVACY ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_update_privacy_endpoint_success(monkeypatch):
    """Test PATCH /users/me/privacy returns 200."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_update_privacy(db, user, data):
        return {
            "success": True,
            "message": "Profile visibility updated.",
            "data": {"is_private": data.is_private},
        }

    monkeypatch.setattr(UserService, "update_privacy", fake_update_privacy)

    response = client.patch("/users/me/privacy", json={"is_private": True})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["is_private"] is True


def test_update_privacy_endpoint_toggle(monkeypatch):
    """Test toggling privacy between public and private."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(
        user_id=user_id, is_private=True
    )

    def fake_update_privacy(db, user, data):
        return {
            "success": True,
            "message": "Profile visibility updated.",
            "data": {"is_private": False},
        }

    monkeypatch.setattr(UserService, "update_privacy", fake_update_privacy)

    response = client.patch("/users/me/privacy", json={"is_private": False})

    assert response.status_code == 200
    assert response.json()["data"]["is_private"] is False


# ────────────────────────────────────────────────────────
# UPLOAD AVATAR ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_upload_avatar_endpoint_success(monkeypatch):
    """Test PUT /users/me/avatar returns 200."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_upload(db, user, file):
        return {
            "success": True,
            "message": "Avatar uploaded successfully.",
            "data": {"profile_picture": f"Uploads/Avatar/{user_id}.jpg"},
        }

    monkeypatch.setattr(UserService, "upload_avatar", fake_upload)

    # Create a fake file for upload
    file_content = b"fake image content"
    response = client.put(
        "/users/me/avatar",
        files={"file": ("avatar.jpg", io.BytesIO(file_content), "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "profile_picture" in body["data"]


def test_upload_avatar_endpoint_invalid_type(monkeypatch):
    """Test PUT /users/me/avatar with invalid file type."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    from fastapi import HTTPException, status

    def fake_upload(db, user, file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WEBP files are allowed",
        )

    monkeypatch.setattr(UserService, "upload_avatar", fake_upload)

    file_content = b"fake pdf content"
    response = client.put(
        "/users/me/avatar",
        files={"file": ("document.pdf", io.BytesIO(file_content), "application/pdf")},
    )

    assert response.status_code == 400


def test_upload_avatar_endpoint_without_auth(monkeypatch):
    """Test PUT /users/me/avatar without authentication returns 401."""
    app.dependency_overrides.pop(get_current_user, None)

    file_content = b"fake image"
    response = client.put(
        "/users/me/avatar", files={"file": ("avatar.jpg", io.BytesIO(file_content))}
    )

    assert response.status_code == 401

    app.dependency_overrides[get_current_user] = lambda: FakeUser()


# ────────────────────────────────────────────────────────
# UPLOAD COVER ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_upload_cover_endpoint_success(monkeypatch):
    """Test PUT /users/me/cover returns 200."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_upload(db, user, file):
        return {
            "success": True,
            "message": "Cover photo uploaded successfully.",
            "data": {"cover_photo": f"Uploads/Cover/{user_id}.jpg"},
        }

    monkeypatch.setattr(UserService, "upload_cover", fake_upload)

    file_content = b"fake image content"
    response = client.put(
        "/users/me/cover",
        files={"file": ("cover.jpg", io.BytesIO(file_content), "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "cover_photo" in body["data"]


# ────────────────────────────────────────────────────────
# GET SOCIAL LINKS ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_get_social_links_endpoint_success(monkeypatch):
    """Test GET /users/me/social-links returns 200."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_get_links(db, user):
        return {
            "success": True,
            "data": {
                "social_links": [
                    {"platform": "twitter", "url": "https://twitter.com/user"},
                    {"platform": "instagram", "url": "https://instagram.com/user"},
                ]
            },
        }

    monkeypatch.setattr(SocialLinkService, "get_social_links", fake_get_links)

    response = client.get("/users/me/social-links")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["social_links"]) == 2


def test_get_social_links_endpoint_empty(monkeypatch):
    """Test GET /users/me/social-links returns empty list."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_get_links(db, user):
        return {"success": True, "data": {"social_links": []}}

    monkeypatch.setattr(SocialLinkService, "get_social_links", fake_get_links)

    response = client.get("/users/me/social-links")

    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["social_links"]) == 0


def test_get_social_links_endpoint_without_auth(monkeypatch):
    """Test GET /users/me/social-links without authentication returns 401."""
    app.dependency_overrides.pop(get_current_user, None)

    response = client.get("/users/me/social-links")

    assert response.status_code == 401

    app.dependency_overrides[get_current_user] = lambda: FakeUser()


# ────────────────────────────────────────────────────────
# UPDATE SOCIAL LINKS ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_update_social_links_endpoint_success(monkeypatch):
    """Test PUT /users/me/social-links returns 200."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_update_links(db, user, data):
        return {
            "success": True,
            "message": "Social links updated successfully.",
            "data": {
                "social_links": [
                    {"platform": "twitter", "url": "https://twitter.com/newuser"},
                    {"platform": "youtube", "url": "https://youtube.com/newuser"},
                ]
            },
        }

    monkeypatch.setattr(SocialLinkService, "update_social_links", fake_update_links)

    response = client.put(
        "/users/me/social-links",
        json={
            "social_links": [
                {"platform": "twitter", "url": "https://twitter.com/newuser"},
                {"platform": "youtube", "url": "https://youtube.com/newuser"},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["social_links"]) == 2


def test_update_social_links_endpoint_clear(monkeypatch):
    """Test PUT /users/me/social-links to clear all links."""
    user_id = uuid.uuid4()

    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_update_links(db, user, data):
        return {
            "success": True,
            "message": "Social links updated successfully.",
            "data": {"social_links": []},
        }

    monkeypatch.setattr(SocialLinkService, "update_social_links", fake_update_links)

    response = client.put("/users/me/social-links", json={"social_links": []})

    assert response.status_code == 200
    assert len(response.json()["data"]["social_links"]) == 0


def test_update_social_links_endpoint_without_auth(monkeypatch):
    """Test PUT /users/me/social-links without authentication returns 401."""
    app.dependency_overrides.pop(get_current_user, None)

    response = client.put(
        "/users/me/social-links",
        json={
            "social_links": [{"platform": "twitter", "url": "https://twitter.com/user"}]
        },
    )

    assert response.status_code == 401

    app.dependency_overrides[get_current_user] = lambda: FakeUser()


# ────────────────────────────────────────────────────────
# CHANGE USERNAME ENDPOINT TESTS
# ────────────────────────────────────────────────────────


def test_change_username_endpoint_success(monkeypatch):
    """Test PATCH /users/me/username returns 200 with new username."""
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    def fake_change_username(db, user, data):
        return {"success": True, "data": {"username": data.username}}

    monkeypatch.setattr(UserService, "change_username", fake_change_username)

    response = client.patch("/users/me/username", json={"username": "newname"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["username"] == "newname"


def test_change_username_endpoint_taken(monkeypatch):
    """Test PATCH /users/me/username returns 409 when username is already taken."""
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    from fastapi import HTTPException, status

    def fake_change_username(db, user, data):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken.",
        )

    monkeypatch.setattr(UserService, "change_username", fake_change_username)

    response = client.patch("/users/me/username", json={"username": "takenname"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken."


def test_change_username_endpoint_invalid_format(monkeypatch):
    """Test PATCH /users/me/username returns 422
    for username with invalid characters."""
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    response = client.patch("/users/me/username", json={"username": "invalid name!"})

    assert response.status_code == 422


def test_change_username_endpoint_too_short(monkeypatch):
    """Test PATCH /users/me/username returns 422 when username is under 3 characters."""
    user_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: FakeUser(user_id=user_id)

    response = client.patch("/users/me/username", json={"username": "ab"})

    assert response.status_code == 422


def test_change_username_endpoint_without_auth(monkeypatch):
    """Test PATCH /users/me/username without authentication returns 401."""
    app.dependency_overrides.pop(get_current_user, None)

    response = client.patch("/users/me/username", json={"username": "newname"})

    assert response.status_code == 401

    app.dependency_overrides[get_current_user] = lambda: FakeUser()

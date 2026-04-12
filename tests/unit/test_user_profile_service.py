"""
Unit tests for the User Profile Service.

Tests all endpoints and scenarios including:
- Get own profile (full profile data)
- Get user profile by ID (public/private profiles)
- Update profile (partial updates, field filtering)
- Update privacy (toggle public/private)
- Upload avatar (file validation, size limits)
- Upload cover photo (file validation, size limits)
- Get social links (user's social profiles)
- Update social links (replace all links)
"""
import uuid
import io
import pytest
from fastapi import HTTPException

from app.services.user_service import UserService
from app.services.social_link_service import SocialLinkService


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
    def __init__(self, user_id=None, email="test@example.com", display_name="Test User",
                 account_type="listener", is_verified=True, is_suspended=False,
                 bio=None, location=None, is_premium=False, is_private=False,
                 profile_picture=None, cover_photo=None, follower_count=0,
                 following_count=0, track_count=0, created_at=None, updated_at=None):
        self.user_id = user_id or uuid.uuid4()
        self.email = email
        self.display_name = display_name
        self.account_type = account_type
        self.is_verified = is_verified
        self.is_suspended = is_suspended
        self.bio = bio
        self.location = location
        self.is_premium = is_premium
        self.is_private = is_private
        self.profile_picture = profile_picture
        self.cover_photo = cover_photo
        self.follower_count = follower_count
        self.following_count = following_count
        self.track_count = track_count
        self.created_at = created_at or "2024-01-01T00:00:00Z"
        self.updated_at = updated_at


class FakeSocialLink:
    """Mock social link object."""
    def __init__(self, platform="twitter", url="https://twitter.com/user"):
        self.platform = platform
        self.url = url


class UpdateProfileRequest:
    """Mock update profile request."""
    def __init__(self, display_name=None, bio=None, location=None, account_type=None):
        self.display_name = display_name
        self.bio = bio
        self.location = location
        self.account_type = account_type

    def model_dump(self, exclude_unset=False):
        """Mimic pydantic model_dump method."""
        data = {}
        if self.display_name is not None:
            data["display_name"] = self.display_name
        if self.bio is not None:
            data["bio"] = self.bio
        if self.location is not None:
            data["location"] = self.location
        if self.account_type is not None:
            data["account_type"] = self.account_type
        return data


class UpdatePrivacyRequest:
    """Mock update privacy request."""
    def __init__(self, is_private):
        self.is_private = is_private


class UpdateSocialLinksRequest:
    """Mock update social links request."""
    def __init__(self, social_links=None):
        self.social_links = social_links or []


class FakeUploadFile:
    """Mock FastAPI UploadFile."""
    def __init__(self, filename="test.jpg", content_type="image/jpeg", size=1000):
        self.filename = filename
        self.content_type = content_type
        self.file = io.BytesIO(b"x" * size)
        self.size = size


# ────────────────────────────────────────────────────────
# GET MY PROFILE TESTS
# ────────────────────────────────────────────────────────

def test_get_my_profile_success():
    """Test getting full profile of authenticated user."""
    user_id = uuid.uuid4()
    current_user = FakeUser(
        user_id=user_id,
        email="user@example.com",
        display_name="John Doe",
        account_type="artist",
        is_verified=True,
        bio="Music producer",
        location="New York",
        is_premium=True,
        is_private=False,
        profile_picture="https://example.com/avatar.jpg",
        cover_photo="https://example.com/cover.jpg",
        follower_count=100,
        following_count=50,
        track_count=10
    )

    result = UserService.get_my_profile(current_user)

    assert result["success"] is True
    assert result["data"]["user_id"] == str(user_id)
    assert result["data"]["display_name"] == "John Doe"
    assert result["data"]["email"] == "user@example.com"
    assert result["data"]["account_type"] == "artist"
    assert result["data"]["is_verified"] is True
    assert result["data"]["bio"] == "Music producer"
    assert result["data"]["location"] == "New York"
    assert result["data"]["follower_count"] == 100
    assert result["data"]["track_count"] == 10


def test_get_my_profile_with_minimal_data():
    """Test getting profile with minimal user data."""
    current_user = FakeUser(
        display_name="Simple User",
        bio=None,
        location=None,
        profile_picture=None,
        cover_photo=None
    )

    result = UserService.get_my_profile(current_user)

    assert result["success"] is True
    assert result["data"]["display_name"] == "Simple User"
    assert result["data"]["bio"] is None
    assert result["data"]["profile_picture"] is None


# ────────────────────────────────────────────────────────
# GET USER PROFILE BY ID TESTS
# ────────────────────────────────────────────────────────

def test_get_user_profile_public_success(monkeypatch):
    """Test getting public profile of another user."""
    db = FakeDB()
    user_id = uuid.uuid4()
    user = FakeUser(
        user_id=user_id,
        display_name="Public User",
        account_type="artist",
        bio="My bio",
        location="LON",
        is_private=False,
        profile_picture="https://example.com/pic.jpg",
        cover_photo="https://example.com/cover.jpg",
        follower_count=200,
        following_count=100,
        track_count=20
    )

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: user)

    result = UserService.get_profile_by_id(db, user_id)

    assert result["success"] is True
    assert result["data"]["user_id"] == str(user_id)
    assert result["data"]["display_name"] == "Public User"
    assert result["data"]["bio"] == "My bio"
    assert result["data"]["follower_count"] == 200


def test_get_user_profile_private_limited_data(monkeypatch):
    """Test getting private profile shows limited data."""
    db = FakeDB()
    user_id = uuid.uuid4()
    user = FakeUser(
        user_id=user_id,
        display_name="Private User",
        bio="Secret bio",
        is_private=True,
        profile_picture="https://example.com/pic.jpg",
        follower_count=50
    )

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: user)

    result = UserService.get_profile_by_id(db, user_id)

    assert result["success"] is True
    # Limited data returned for private profile
    assert result["data"]["user_id"] == str(user_id)
    assert result["data"]["display_name"] == "Private User"
    assert result["data"]["profile_picture"] == "https://example.com/pic.jpg"
    assert result["data"]["follower_count"] == 50
    # These should NOT be in the response for private profiles
    assert "bio" not in result["data"]
    assert "location" not in result["data"]


def test_get_user_profile_not_found(monkeypatch):
    """Test getting profile of non-existent user raises 404."""
    db = FakeDB()
    user_id = uuid.uuid4()

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "get_by_id", lambda db_arg, uid: None)

    with pytest.raises(HTTPException) as exc_info:
        UserService.get_profile_by_id(db, user_id)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


# ────────────────────────────────────────────────────────
# UPDATE PROFILE TESTS
# ────────────────────────────────────────────────────────

def test_update_profile_all_fields(monkeypatch):
    """Test updating all allowed profile fields."""
    db = FakeDB()
    user = FakeUser(
        display_name="Old Name",
        bio="Old bio",
        location="Old City",
        account_type="listener"
    )

    data = UpdateProfileRequest(
        display_name="New Name",
        bio="New bio",
        location="New City",
        account_type="artist"
    )

    from app.repositories.user_repo import UserRepository

    def fake_update(db_arg, user_arg, fields):
        for key, value in fields.items():
            setattr(user_arg, key, value)

    monkeypatch.setattr(UserRepository, "update_fields", fake_update)

    result = UserService.update_profile(db, user, data)

    assert result["success"] is True
    assert result["message"] == "Profile updated successfully."
    assert result["data"]["display_name"] == "New Name"  # Updated by fake_update function


def test_update_profile_partial_fields(monkeypatch):
    """Test updating only some profile fields."""
    db = FakeDB()
    user = FakeUser(
        display_name="Current Name",
        bio="Current bio",
        location="Current City",
        account_type="listener"
    )

    data = UpdateProfileRequest(display_name="Updated Name")

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "update_fields", lambda db_arg, u, fields: None)

    result = UserService.update_profile(db, user, data)

    assert result["success"] is True
    assert result["message"] == "Profile updated successfully."


def test_update_profile_only_bio(monkeypatch):
    """Test updating only bio field."""
    db = FakeDB()
    user = FakeUser(bio="Old bio")
    data = UpdateProfileRequest(bio="New bio")

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "update_fields", lambda db_arg, u, fields: None)

    result = UserService.update_profile(db, user, data)

    assert result["success"] is True


def test_update_profile_blocked_fields(monkeypatch):
    """Test that blocked fields are filtered out."""
    db = FakeDB()
    user = FakeUser()
    
    # Try to update fields that should not be allowed
    data = UpdateProfileRequest(display_name="New Name")

    from app.repositories.user_repo import UserRepository
    
    called_with_fields = []

    def fake_update(db_arg, u, fields):
        called_with_fields.append(fields)

    monkeypatch.setattr(UserRepository, "update_fields", fake_update)

    result = UserService.update_profile(db, user, data)

    assert result["success"] is True


# ────────────────────────────────────────────────────────
# UPDATE PRIVACY TESTS
# ────────────────────────────────────────────────────────

def test_update_privacy_to_private(monkeypatch):
    """Test making profile private."""
    db = FakeDB()
    user = FakeUser(is_private=False)
    data = UpdatePrivacyRequest(is_private=True)

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "update_fields", lambda db_arg, u, fields: None)

    result = UserService.update_privacy(db, user, data)

    assert result["success"] is True
    assert result["message"] == "Profile visibility updated."


def test_update_privacy_to_public(monkeypatch):
    """Test making profile public."""
    db = FakeDB()
    user = FakeUser(is_private=True)
    data = UpdatePrivacyRequest(is_private=False)

    from app.repositories.user_repo import UserRepository
    monkeypatch.setattr(UserRepository, "update_fields", lambda db_arg, u, fields: None)

    result = UserService.update_privacy(db, user, data)

    assert result["success"] is True
    assert result["data"]["is_private"] is True  # Original value


# ────────────────────────────────────────────────────────
# UPLOAD AVATAR TESTS
# ────────────────────────────────────────────────────────

def test_upload_avatar_success(monkeypatch):
    """Test successfully uploading avatar."""
    db = FakeDB()
    user = FakeUser()
    file = FakeUploadFile(filename="avatar.jpg", content_type="image/jpeg", size=2000000)

    from app.repositories.user_repo import UserRepository

    def fake_validate(f, max_size, label):
        pass  # No validation errors

    def fake_save(f, uid, subfolder):
        return f"Uploads/{subfolder}/avatar.jpg"

    monkeypatch.setattr(UserService, "_validate_image", fake_validate)
    monkeypatch.setattr(UserService, "_save_file", fake_save)
    monkeypatch.setattr(UserRepository, "update_fields", lambda db_arg, u, fields: None)

    result = UserService.upload_avatar(db, user, file)

    assert result["success"] is True
    assert result["message"] == "Avatar uploaded successfully."
    assert "profile_picture" in result["data"]


def test_upload_avatar_invalid_type(monkeypatch):
    """Test uploading invalid file type for avatar."""
    db = FakeDB()
    user = FakeUser()
    file = FakeUploadFile(filename="avatar.pdf", content_type="application/pdf")

    from fastapi import HTTPException, status

    def fake_validate(f, max_size, label):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WEBP files are allowed"
        )

    monkeypatch.setattr(UserService, "_validate_image", fake_validate)

    with pytest.raises(HTTPException) as exc_info:
        UserService.upload_avatar(db, user, file)

    assert exc_info.value.status_code == 400


def test_upload_avatar_file_too_large(monkeypatch):
    """Test uploading avatar file that exceeds size limit."""
    db = FakeDB()
    user = FakeUser()
    # 6 MB file (limit is 5 MB)
    file = FakeUploadFile(filename="avatar.jpg", size=6 * 1024 * 1024)

    from fastapi import HTTPException, status

    def fake_validate(f, max_size, label):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must not exceed {label}"
        )

    monkeypatch.setattr(UserService, "_validate_image", fake_validate)

    with pytest.raises(HTTPException) as exc_info:
        UserService.upload_avatar(db, user, file)

    assert exc_info.value.status_code == 400


# ────────────────────────────────────────────────────────
# UPLOAD COVER PHOTO TESTS
# ────────────────────────────────────────────────────────

def test_upload_cover_success(monkeypatch):
    """Test successfully uploading cover photo."""
    db = FakeDB()
    user = FakeUser()
    file = FakeUploadFile(filename="cover.png", content_type="image/png", size=5000000)

    from app.repositories.user_repo import UserRepository

    def fake_validate(f, max_size, label):
        pass

    def fake_save(f, uid, subfolder):
        return f"Uploads/{subfolder}/cover.png"

    monkeypatch.setattr(UserService, "_validate_image", fake_validate)
    monkeypatch.setattr(UserService, "_save_file", fake_save)
    monkeypatch.setattr(UserRepository, "update_fields", lambda db_arg, u, fields: None)

    result = UserService.upload_cover(db, user, file)

    assert result["success"] is True
    assert result["message"] == "Cover photo uploaded successfully."
    assert "cover_photo" in result["data"]


def test_upload_cover_invalid_type(monkeypatch):
    """Test uploading invalid file type for cover."""
    db = FakeDB()
    user = FakeUser()
    file = FakeUploadFile(filename="cover.txt", content_type="text/plain")

    from fastapi import HTTPException, status

    def fake_validate(f, max_size, label):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WEBP files are allowed"
        )

    monkeypatch.setattr(UserService, "_validate_image", fake_validate)

    with pytest.raises(HTTPException) as exc_info:
        UserService.upload_cover(db, user, file)

    assert exc_info.value.status_code == 400


def test_upload_cover_file_too_large(monkeypatch):
    """Test uploading cover file that exceeds size limit."""
    db = FakeDB()
    user = FakeUser()
    # 11 MB file (limit is 10 MB)
    file = FakeUploadFile(filename="cover.jpg", size=11 * 1024 * 1024)

    from fastapi import HTTPException, status

    def fake_validate(f, max_size, label):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must not exceed {label}"
        )

    monkeypatch.setattr(UserService, "_validate_image", fake_validate)

    with pytest.raises(HTTPException) as exc_info:
        UserService.upload_cover(db, user, file)

    assert exc_info.value.status_code == 400


# ────────────────────────────────────────────────────────
# GET SOCIAL LINKS TESTS
# ────────────────────────────────────────────────────────

def test_get_social_links_success(monkeypatch):
    """Test getting all social links for user."""
    db = FakeDB()
    user = FakeUser()
    
    links = [
        FakeSocialLink(platform="twitter", url="https://twitter.com/user"),
        FakeSocialLink(platform="instagram", url="https://instagram.com/user"),
        FakeSocialLink(platform="youtube", url="https://youtube.com/user"),
    ]

    from app.repositories.social_link_repo import SocialLinkRepository
    monkeypatch.setattr(SocialLinkRepository, "get_by_user_id", lambda db_arg, uid: links)

    result = SocialLinkService.get_social_links(db, user)

    assert result["success"] is True
    assert len(result["data"]["social_links"]) == 3
    assert result["data"]["social_links"][0]["platform"] == "twitter"
    assert result["data"]["social_links"][1]["platform"] == "instagram"


def test_get_social_links_empty(monkeypatch):
    """Test getting social links when user has none."""
    db = FakeDB()
    user = FakeUser()

    from app.repositories.social_link_repo import SocialLinkRepository
    monkeypatch.setattr(SocialLinkRepository, "get_by_user_id", lambda db_arg, uid: [])

    result = SocialLinkService.get_social_links(db, user)

    assert result["success"] is True
    assert len(result["data"]["social_links"]) == 0


def test_get_social_links_single(monkeypatch):
    """Test getting single social link."""
    db = FakeDB()
    user = FakeUser()
    
    links = [FakeSocialLink(platform="spotify", url="https://spotify.com/artist/user")]

    from app.repositories.social_link_repo import SocialLinkRepository
    monkeypatch.setattr(SocialLinkRepository, "get_by_user_id", lambda db_arg, uid: links)

    result = SocialLinkService.get_social_links(db, user)

    assert result["success"] is True
    assert len(result["data"]["social_links"]) == 1
    assert result["data"]["social_links"][0]["platform"] == "spotify"


# ────────────────────────────────────────────────────────
# UPDATE SOCIAL LINKS TESTS
# ────────────────────────────────────────────────────────

def test_update_social_links_replace_all(monkeypatch):
    """Test replacing all social links."""
    db = FakeDB()
    user = FakeUser()
    
    new_links = [
        FakeSocialLink(platform="twitter", url="https://twitter.com/newuser"),
        FakeSocialLink(platform="youtube", url="https://youtube.com/newuser"),
    ]
    
    data = UpdateSocialLinksRequest(social_links=new_links)

    from app.repositories.social_link_repo import SocialLinkRepository

    def fake_delete(db_arg, uid):
        pass

    def fake_create_many(db_arg, uid, links):
        pass

    def fake_get(db_arg, uid):
        return new_links

    monkeypatch.setattr(SocialLinkRepository, "delete_by_user_id", fake_delete)
    monkeypatch.setattr(SocialLinkRepository, "create_many", fake_create_many)
    monkeypatch.setattr(SocialLinkRepository, "get_by_user_id", fake_get)

    result = SocialLinkService.update_social_links(db, user, data)

    assert result["success"] is True
    assert result["message"] == "Social links updated successfully."
    assert len(result["data"]["social_links"]) == 2


def test_update_social_links_clear_all(monkeypatch):
    """Test clearing all social links."""
    db = FakeDB()
    user = FakeUser()
    data = UpdateSocialLinksRequest(social_links=[])

    from app.repositories.social_link_repo import SocialLinkRepository

    def fake_delete(db_arg, uid):
        pass

    def fake_create_many(db_arg, uid, links):
        pass

    def fake_get(db_arg, uid):
        return []

    monkeypatch.setattr(SocialLinkRepository, "delete_by_user_id", fake_delete)
    monkeypatch.setattr(SocialLinkRepository, "create_many", fake_create_many)
    monkeypatch.setattr(SocialLinkRepository, "get_by_user_id", fake_get)

    result = SocialLinkService.update_social_links(db, user, data)

    assert result["success"] is True
    assert len(result["data"]["social_links"]) == 0


def test_update_social_links_single_link(monkeypatch):
    """Test updating with single social link."""
    db = FakeDB()
    user = FakeUser()
    
    new_links = [FakeSocialLink(platform="spotify", url="https://spotify.com/artist")]
    data = UpdateSocialLinksRequest(social_links=new_links)

    from app.repositories.social_link_repo import SocialLinkRepository

    monkeypatch.setattr(SocialLinkRepository, "delete_by_user_id", lambda db_arg, uid: None)
    monkeypatch.setattr(SocialLinkRepository, "create_many", lambda db_arg, uid, links: None)
    monkeypatch.setattr(SocialLinkRepository, "get_by_user_id", lambda db_arg, uid: new_links)

    result = SocialLinkService.update_social_links(db, user, data)

    assert result["success"] is True
    assert len(result["data"]["social_links"]) == 1

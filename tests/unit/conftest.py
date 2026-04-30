"""
Shared pytest fixtures for unit tests.

Provides mock database sessions, mock user objects, and
other reusable test helpers so individual test files stay clean.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

# ── Fake User helper ───────────────────────────────────


def make_fake_user(**overrides):
    """
    Build a MagicMock that looks like a User ORM object.

    Any keyword argument overrides the default value.
    """
    defaults = {
        "user_id": uuid.uuid4(),
        "email": "test@example.com",
        "username": "testuser",
        "password_hash": "$2b$12$hashedpasswordplaceholder",
        "display_name": "TestUser",
        "account_type": "listener",
        "role": "user",
        "is_verified": True,
        "is_suspended": False,
        "CAPTCHA_verified": False,
        "bio": None,
        "location": None,
        "is_premium": False,
        "billing_cycle": None,
        "subscription_tier": None,
        "is_private": False,
        "profile_picture": None,
        "cover_photo": None,
        "follower_count": 0,
        "following_count": 0,
        "track_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    defaults.update(overrides)
    user = MagicMock()
    for key, value in defaults.items():
        setattr(user, key, value)
    return user


# ── Fixtures ───────────────────────────────────────────


@pytest.fixture
def mock_db():
    """Return a MagicMock pretending to be a SQLAlchemy Session."""
    return MagicMock()


@pytest.fixture
def verified_user():
    """Return a verified, non-suspended user."""
    return make_fake_user()


@pytest.fixture
def unverified_user():
    """Return a user whose email is NOT yet verified."""
    return make_fake_user(is_verified=False)


@pytest.fixture
def suspended_user():
    """Return a verified but suspended user."""
    return make_fake_user(is_suspended=True)


@pytest.fixture
def private_user():
    """Return a user whose profile is set to private."""
    return make_fake_user(is_private=True)

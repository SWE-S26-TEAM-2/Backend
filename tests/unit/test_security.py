"""
Unit tests for app.core.security module.

Tests password hashing/verification and JWT token
creation/decoding for both access and refresh tokens.
"""

import uuid
from unittest.mock import patch  # noqa: F401

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

# ── Password hashing ──────────────────────────────────


class TestHashPassword:
    """Tests for hash_password()."""

    def test_returns_bcrypt_string(self):
        """Hashed output should start with the '$2b$' bcrypt prefix."""
        hashed = hash_password("MySecret123")
        assert hashed.startswith("$2b$")

    def test_different_passwords_produce_different_hashes(self):
        """Two distinct passwords must never produce the same hash."""
        h1 = hash_password("PasswordA1")
        h2 = hash_password("PasswordB2")
        assert h1 != h2

    def test_same_password_produces_different_hashes(self):
        """Bcrypt uses a random salt, so the same input gives
        different outputs each time."""
        h1 = hash_password("Same1234")
        h2 = hash_password("Same1234")
        assert h1 != h2


class TestVerifyPassword:
    """Tests for verify_password()."""

    def test_correct_password_returns_true(self):
        """verify_password should return True for the original plain text."""
        hashed = hash_password("Correct1")
        assert verify_password("Correct1", hashed) is True

    def test_wrong_password_returns_false(self):
        """verify_password should return False for a wrong plain text."""
        hashed = hash_password("Correct1")
        assert verify_password("Wrong999", hashed) is False


# ── Access tokens ──────────────────────────────────────


class TestAccessToken:
    """Tests for create_access_token() and decode_access_token()."""

    def test_create_and_decode_roundtrip(self):
        """A freshly created access token should decode back to
        the same user_id."""
        uid = str(uuid.uuid4())
        token = create_access_token(uid)
        payload = decode_access_token(token)
        assert payload["sub"] == uid
        assert payload["type"] == "access"

    def test_decode_rejects_refresh_token(self):
        """decode_access_token must reject a token whose type is 'refresh'."""
        uid = str(uuid.uuid4())
        refresh = create_refresh_token(uid)
        with pytest.raises(JWTError):
            decode_access_token(refresh)

    def test_decode_rejects_garbage(self):
        """decode_access_token must raise JWTError for invalid strings."""
        with pytest.raises(JWTError):
            decode_access_token("not.a.token")


# ── Refresh tokens ─────────────────────────────────────


class TestRefreshToken:
    """Tests for create_refresh_token() and decode_refresh_token()."""

    def test_create_and_decode_roundtrip(self):
        """A freshly created refresh token should decode back to
        the same user_id and include a jti."""
        uid = str(uuid.uuid4())
        token = create_refresh_token(uid)
        payload = decode_refresh_token(token)
        assert payload["sub"] == uid
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_decode_rejects_access_token(self):
        """decode_refresh_token must reject a token whose type is 'access'."""
        uid = str(uuid.uuid4())
        access = create_access_token(uid)
        with pytest.raises(JWTError):
            decode_refresh_token(access)

    def test_each_refresh_token_has_unique_jti(self):
        """Two refresh tokens for the same user must have different jtis."""
        uid = str(uuid.uuid4())
        t1 = decode_refresh_token(create_refresh_token(uid))
        t2 = decode_refresh_token(create_refresh_token(uid))
        assert t1["jti"] != t2["jti"]

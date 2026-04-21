"""
Unit tests for app.services.auth_service.AuthService.

Every repository / security call is mocked so we test
only the business logic — no database required.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.auth_service import AuthService
from tests.unit.conftest import make_fake_user

# ── Helpers ────────────────────────────────────────────


def _register_data(
    email="new@example.com",
    password="StrongPass1",
    display_name="NewUser",
    account_type="listener",
):
    """Return a MagicMock that looks like a RegisterRequest."""
    data = MagicMock()
    data.email = email
    data.password = password
    data.display_name = display_name
    data.account_type = account_type
    return data


def _login_data(email="test@example.com", password="Pass1234"):
    data = MagicMock()
    data.email = email
    data.password = password
    return data


def _google_data(google_token="google-id-token"):
    data = MagicMock()
    data.google_token = google_token
    return data


def _verify_email_data(token="some-token"):
    data = MagicMock()
    data.token = token
    return data


def _resend_data(email="test@example.com"):
    data = MagicMock()
    data.email = email
    return data


def _refresh_data(refresh_token="tok"):
    data = MagicMock()
    data.refresh_token = refresh_token
    return data


def _logout_data(refresh_token="tok"):
    data = MagicMock()
    data.refresh_token = refresh_token
    return data


def _forgot_data(email="test@example.com"):
    data = MagicMock()
    data.email = email
    return data


def _reset_data(token="reset-tok", new_password="NewPass123"):
    data = MagicMock()
    data.token = token
    data.new_password = new_password
    return data


# ══════════════════════════════════════════════════════
#  register_user
# ══════════════════════════════════════════════════════


class TestRegisterUser:
    """Tests for AuthService.register_user."""

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    @patch("app.services.auth_service.hash_password", return_value="hashed")
    def test_success(self, mock_hash, mock_user_repo, mock_token_repo, mock_db):
        """Registering with a fresh email should succeed and return user data."""
        mock_user_repo.get_by_email.return_value = None
        created_user = make_fake_user(email="new@example.com")
        mock_user_repo.create.return_value = created_user

        result = AuthService.register_user(mock_db, _register_data())

        assert result["success"] is True
        mock_user_repo.create.assert_called_once()
        mock_token_repo.create.assert_called_once()

    @patch("app.services.auth_service.UserRepository")
    def test_duplicate_email_raises_409(self, mock_user_repo, mock_db):
        """Registering with an existing email should raise 409."""
        mock_user_repo.get_by_email.return_value = make_fake_user()

        with pytest.raises(HTTPException) as exc:
            AuthService.register_user(mock_db, _register_data())
        assert exc.value.status_code == 409


# ══════════════════════════════════════════════════════
#  verify_email
# ══════════════════════════════════════════════════════


class TestVerifyEmail:
    """Tests for AuthService.verify_email."""

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_success(self, mock_user_repo, mock_token_repo, mock_db):
        """A valid, unused, non-expired token should verify the user."""
        token_rec = MagicMock()
        token_rec.used = False
        token_rec.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        token_rec.user_id = uuid.uuid4()
        mock_token_repo.get_by_token.return_value = token_rec
        mock_user_repo.get_by_id.return_value = make_fake_user()

        result = AuthService.verify_email(mock_db, _verify_email_data())
        assert result["success"] is True

    @patch("app.services.auth_service.TokenRepository")
    def test_invalid_token_raises_400(self, mock_token_repo, mock_db):
        """A token that doesn't exist should raise 400."""
        mock_token_repo.get_by_token.return_value = None

        with pytest.raises(HTTPException) as exc:
            AuthService.verify_email(mock_db, _verify_email_data())
        assert exc.value.status_code == 400

    @patch("app.services.auth_service.TokenRepository")
    def test_used_token_raises_400(self, mock_token_repo, mock_db):
        """A token already used should raise 400."""
        token_rec = MagicMock()
        token_rec.used = True
        mock_token_repo.get_by_token.return_value = token_rec

        with pytest.raises(HTTPException) as exc:
            AuthService.verify_email(mock_db, _verify_email_data())
        assert exc.value.status_code == 400

    @patch("app.services.auth_service.TokenRepository")
    def test_expired_token_raises_410(self, mock_token_repo, mock_db):
        """An expired token should raise 410 GONE."""
        token_rec = MagicMock()
        token_rec.used = False
        token_rec.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_token_repo.get_by_token.return_value = token_rec

        with pytest.raises(HTTPException) as exc:
            AuthService.verify_email(mock_db, _verify_email_data())
        assert exc.value.status_code == 410


# ══════════════════════════════════════════════════════
#  resend_verification
# ══════════════════════════════════════════════════════


class TestResendVerification:
    """Tests for AuthService.resend_verification."""

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_success(self, mock_user_repo, mock_token_repo, mock_db):
        """Resend should succeed for an unverified user under the rate limit."""
        mock_user_repo.get_by_email.return_value = make_fake_user(is_verified=False)
        mock_token_repo.count_recent_for_email.return_value = 0

        result = AuthService.resend_verification(mock_db, _resend_data())
        assert result["success"] is True

    @patch("app.services.auth_service.UserRepository")
    def test_unknown_email_raises_404(self, mock_user_repo, mock_db):
        """An email that doesn't exist should raise 404."""
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(HTTPException) as exc:
            AuthService.resend_verification(mock_db, _resend_data())
        assert exc.value.status_code == 404

    @patch("app.services.auth_service.UserRepository")
    def test_already_verified_raises_409(self, mock_user_repo, mock_db):
        """A user who is already verified should raise 409."""
        mock_user_repo.get_by_email.return_value = make_fake_user(is_verified=True)

        with pytest.raises(HTTPException) as exc:
            AuthService.resend_verification(mock_db, _resend_data())
        assert exc.value.status_code == 409

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_rate_limit_raises_429(self, mock_user_repo, mock_token_repo, mock_db):
        """Exceeding 3 active tokens should raise 429."""
        mock_user_repo.get_by_email.return_value = make_fake_user(is_verified=False)
        mock_token_repo.count_recent_for_email.return_value = 3

        with pytest.raises(HTTPException) as exc:
            AuthService.resend_verification(mock_db, _resend_data())
        assert exc.value.status_code == 429


# ══════════════════════════════════════════════════════
#  login_user
# ══════════════════════════════════════════════════════


class TestLoginUser:
    """Tests for AuthService.login_user."""

    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.decode_refresh_token")
    @patch("app.services.auth_service.create_refresh_token", return_value="rt")
    @patch("app.services.auth_service.create_access_token", return_value="at")
    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_success(
        self,
        mock_user_repo,
        mock_verify,
        mock_at,
        mock_rt,
        mock_decode,
        mock_rt_repo,
        mock_db,
    ):
        """Valid credentials for a verified user should return tokens."""
        mock_user_repo.get_by_email.return_value = make_fake_user()
        mock_decode.return_value = {"jti": str(uuid.uuid4()), "sub": "x"}

        result = AuthService.login_user(mock_db, _login_data())
        assert result["success"] is True
        assert result["data"]["access_token"] == "at"

    @patch("app.services.auth_service.verify_password", return_value=False)
    @patch("app.services.auth_service.UserRepository")
    def test_wrong_password_raises_401(self, mock_user_repo, mock_verify, mock_db):
        """Wrong password should raise 401."""
        mock_user_repo.get_by_email.return_value = make_fake_user()

        with pytest.raises(HTTPException) as exc:
            AuthService.login_user(mock_db, _login_data())
        assert exc.value.status_code == 401

    @patch("app.services.auth_service.UserRepository")
    def test_unknown_email_raises_401(self, mock_user_repo, mock_db):
        """Email not found should raise 401 (same as wrong password)."""
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(HTTPException) as exc:
            AuthService.login_user(mock_db, _login_data())
        assert exc.value.status_code == 401

    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_unverified_raises_403(self, mock_user_repo, mock_verify, mock_db):
        """An unverified user should raise 403."""
        mock_user_repo.get_by_email.return_value = make_fake_user(is_verified=False)

        with pytest.raises(HTTPException) as exc:
            AuthService.login_user(mock_db, _login_data())
        assert exc.value.status_code == 403

    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_suspended_raises_403(self, mock_user_repo, mock_verify, mock_db):
        """A suspended user should raise 403."""
        mock_user_repo.get_by_email.return_value = make_fake_user(is_suspended=True)

        with pytest.raises(HTTPException) as exc:
            AuthService.login_user(mock_db, _login_data())
        assert exc.value.status_code == 403


# ══════════════════════════════════════════════════════
#  refresh_access_token
# ══════════════════════════════════════════════════════


class TestGoogleLogin:
    """Tests for AuthService.google_login."""

    @patch("app.services.auth_service.GOOGLE_CLIENT_ID_ANDROID", "android-client")
    @patch("app.services.auth_service.GOOGLE_CLIENT_ID_IOS", "ios-client")
    @patch("app.services.auth_service.GOOGLE_CLIENT_ID_WEB", "web-client")
    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.decode_refresh_token")
    @patch("app.services.auth_service.create_refresh_token", return_value="rt")
    @patch("app.services.auth_service.create_access_token", return_value="at")
    @patch("app.services.auth_service.UserRepository")
    @patch("app.services.auth_service.id_token.verify_oauth2_token")
    def test_accepts_ios_client_id(
        self,
        mock_verify_google,
        mock_user_repo,
        mock_at,
        mock_rt,
        mock_decode,
        mock_rt_repo,
        mock_db,
    ):
        """A Google ID token issued to the iOS client should be accepted."""
        mock_verify_google.side_effect = [
            ValueError("wrong audience"),
            {
                "email": "ios@example.com",
                "name": "iOS User",
                "picture": "https://example.com/avatar.png",
            },
        ]
        mock_user_repo.get_by_email.return_value = make_fake_user(
            email="ios@example.com",
            display_name="iOS User",
        )
        mock_decode.return_value = {"jti": str(uuid.uuid4()), "sub": "x"}

        result = AuthService.google_login(mock_db, _google_data())

        assert result["success"] is True
        assert result["data"]["access_token"] == "at"
        assert mock_verify_google.call_count == 2
        assert mock_verify_google.call_args_list[1].args[2] == "ios-client"


class TestRefreshAccessToken:
    """Tests for AuthService.refresh_access_token."""

    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.create_refresh_token", return_value="new_rt")
    @patch("app.services.auth_service.create_access_token", return_value="new_at")
    @patch("app.services.auth_service.UserRepository")
    @patch("app.services.auth_service.decode_refresh_token")
    def test_success(
        self,
        mock_decode,
        mock_user_repo,
        mock_at,
        mock_rt,
        mock_rt_repo,
        mock_db,
    ):
        """A valid, non-revoked refresh token should return new tokens."""
        uid = str(uuid.uuid4())
        jti = str(uuid.uuid4())
        mock_decode.return_value = {"sub": uid, "jti": jti}
        token_rec = MagicMock()
        token_rec.revoked = False
        mock_rt_repo.get_by_jti.return_value = token_rec
        mock_user_repo.get_by_id.return_value = make_fake_user()

        result = AuthService.refresh_access_token(mock_db, _refresh_data())
        assert result["success"] is True
        assert result["data"]["access_token"] == "new_at"

    @patch("app.services.auth_service.decode_refresh_token")
    def test_invalid_token_raises_401(self, mock_decode, mock_db):
        """If decode raises JWTError, the service should raise 401."""
        from jose import JWTError

        mock_decode.side_effect = JWTError("bad")

        with pytest.raises(HTTPException) as exc:
            AuthService.refresh_access_token(mock_db, _refresh_data())
        assert exc.value.status_code == 401

    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.decode_refresh_token")
    def test_revoked_token_raises_401(self, mock_decode, mock_rt_repo, mock_db):
        """A revoked token should raise 401."""
        mock_decode.return_value = {"sub": "x", "jti": "y"}
        token_rec = MagicMock()
        token_rec.revoked = True
        mock_rt_repo.get_by_jti.return_value = token_rec

        with pytest.raises(HTTPException) as exc:
            AuthService.refresh_access_token(mock_db, _refresh_data())
        assert exc.value.status_code == 401


# ══════════════════════════════════════════════════════
#  logout
# ══════════════════════════════════════════════════════


class TestLogout:
    """Tests for AuthService.logout."""

    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.decode_refresh_token")
    def test_success(self, mock_decode, mock_rt_repo, mock_db):
        """Logout should revoke all tokens and return success."""
        mock_decode.return_value = {"jti": "some-jti"}
        user = make_fake_user()

        result = AuthService.logout(mock_db, _logout_data(), user)
        assert result["success"] is True
        mock_rt_repo.revoke_all_for_user.assert_called_once()

    @patch("app.services.auth_service.decode_refresh_token")
    def test_invalid_refresh_token_raises_400(self, mock_decode, mock_db):
        """If the refresh token is invalid, logout should raise 400."""
        from jose import JWTError

        mock_decode.side_effect = JWTError("bad")

        with pytest.raises(HTTPException) as exc:
            AuthService.logout(mock_db, _logout_data(), make_fake_user())
        assert exc.value.status_code == 400


# ══════════════════════════════════════════════════════
#  forgot_password
# ══════════════════════════════════════════════════════


class TestForgotPassword:
    """Tests for AuthService.forgot_password."""

    @patch("app.services.auth_service.PasswordResetRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_existing_email_success(self, mock_user_repo, mock_pr_repo, mock_db):
        """Known email under the rate limit should create a token."""
        mock_user_repo.get_by_email.return_value = make_fake_user()
        mock_pr_repo.count_recent.return_value = 0

        result = AuthService.forgot_password(mock_db, _forgot_data())
        assert result["success"] is True
        mock_pr_repo.create.assert_called_once()

    @patch("app.services.auth_service.UserRepository")
    def test_unknown_email_still_returns_success(self, mock_user_repo, mock_db):
        """Unknown email should still return a generic 200 (no enumeration)."""
        mock_user_repo.get_by_email.return_value = None

        result = AuthService.forgot_password(mock_db, _forgot_data())
        assert result["success"] is True

    @patch("app.services.auth_service.PasswordResetRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_rate_limit_raises_429(self, mock_user_repo, mock_pr_repo, mock_db):
        """Exceeding 3 active resets should raise 429."""
        mock_user_repo.get_by_email.return_value = make_fake_user()
        mock_pr_repo.count_recent.return_value = 3

        with pytest.raises(HTTPException) as exc:
            AuthService.forgot_password(mock_db, _forgot_data())
        assert exc.value.status_code == 429


# ══════════════════════════════════════════════════════
#  reset_password
# ══════════════════════════════════════════════════════


class TestResetPassword:
    """Tests for AuthService.reset_password."""

    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.PasswordResetRepository")
    @patch("app.services.auth_service.UserRepository")
    @patch("app.services.auth_service.hash_password", return_value="newhash")
    def test_success(
        self,
        mock_hash,
        mock_user_repo,
        mock_pr_repo,
        mock_rt_repo,
        mock_db,
    ):
        """Valid, unused, non-expired token should reset the password."""
        token_rec = MagicMock()
        token_rec.used = False
        token_rec.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        token_rec.user_id = uuid.uuid4()
        mock_pr_repo.get_by_token.return_value = token_rec
        mock_user_repo.get_by_id.return_value = make_fake_user()

        result = AuthService.reset_password(mock_db, _reset_data())
        assert result["success"] is True
        mock_user_repo.update_password.assert_called_once()
        mock_rt_repo.revoke_all_for_user.assert_called_once()

    @patch("app.services.auth_service.PasswordResetRepository")
    def test_invalid_token_raises_400(self, mock_pr_repo, mock_db):
        """A missing token should raise 400."""
        mock_pr_repo.get_by_token.return_value = None

        with pytest.raises(HTTPException) as exc:
            AuthService.reset_password(mock_db, _reset_data())
        assert exc.value.status_code == 400

    @patch("app.services.auth_service.PasswordResetRepository")
    def test_expired_token_raises_410(self, mock_pr_repo, mock_db):
        """An expired reset token should raise 410."""
        token_rec = MagicMock()
        token_rec.used = False
        token_rec.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_pr_repo.get_by_token.return_value = token_rec

        with pytest.raises(HTTPException) as exc:
            AuthService.reset_password(mock_db, _reset_data())
        assert exc.value.status_code == 410

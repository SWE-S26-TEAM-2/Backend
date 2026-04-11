"""Tests for AuthService — Module 1 (Authentication)."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException

from app.services.auth_service import AuthService


class TestRegisterUser:
    """Tests for AuthService.register_user()"""

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_register_success(self, mock_user_repo, mock_token_repo, mock_db):
        mock_user_repo.get_by_email.return_value = None

        data = MagicMock()
        data.email = "new@example.com"
        data.password = "StrongPass1!"
        data.display_name = "New User"
        data.account_type = "listener"

        result = AuthService.register_user(mock_db, data)

        assert result["success"] is True
        assert "Registration successful" in result["message"]
        mock_user_repo.create.assert_called_once()

    @patch("app.services.auth_service.UserRepository")
    def test_register_duplicate_email(self, mock_user_repo, mock_db,
                                      verified_user):
        mock_user_repo.get_by_email.return_value = verified_user

        data = MagicMock()
        data.email = "test@example.com"

        with pytest.raises(HTTPException) as exc:
            AuthService.register_user(mock_db, data)
        assert exc.value.status_code == 409


class TestLoginUser:
    """Tests for AuthService.login_user()"""

    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_login_success(self, mock_user_repo, mock_verify,
                           mock_refresh_repo, mock_db, verified_user):
        mock_user_repo.get_by_email.return_value = verified_user

        data = MagicMock()
        data.email = "test@example.com"
        data.password = "StrongPass1!"

        result = AuthService.login_user(mock_db, data)
        assert result["success"] is True
        assert "access_token" in result["data"]
        assert "refresh_token" in result["data"]
        assert result["data"]["token_type"] == "bearer"
        assert result["data"]["expires_in"] == 900

    @patch("app.services.auth_service.verify_password", return_value=False)
    @patch("app.services.auth_service.UserRepository")
    def test_login_wrong_password(self, mock_user_repo, mock_verify,
                                  mock_db, verified_user):
        mock_user_repo.get_by_email.return_value = verified_user

        data = MagicMock()
        data.email = "test@example.com"
        data.password = "WrongPass1!"

        with pytest.raises(HTTPException) as exc:
            AuthService.login_user(mock_db, data)
        assert exc.value.status_code == 401

    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_login_unverified_user(self, mock_user_repo, mock_verify,
                                   mock_db, unverified_user):
        mock_user_repo.get_by_email.return_value = unverified_user

        data = MagicMock()
        data.email = "test@example.com"
        data.password = "StrongPass1!"

        with pytest.raises(HTTPException) as exc:
            AuthService.login_user(mock_db, data)
        assert exc.value.status_code == 403
        assert "not verified" in exc.value.detail

    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_login_suspended_user(self, mock_user_repo, mock_verify,
                                  mock_db, suspended_user):
        mock_user_repo.get_by_email.return_value = suspended_user

        data = MagicMock()
        data.email = "test@example.com"
        data.password = "StrongPass1!"

        with pytest.raises(HTTPException) as exc:
            AuthService.login_user(mock_db, data)
        assert exc.value.status_code == 403

    @patch("app.services.auth_service.UserRepository")
    def test_login_nonexistent_email(self, mock_user_repo, mock_db):
        mock_user_repo.get_by_email.return_value = None

        data = MagicMock()
        data.email = "noone@example.com"
        data.password = "StrongPass1!"

        with pytest.raises(HTTPException) as exc:
            AuthService.login_user(mock_db, data)
        assert exc.value.status_code == 401


class TestVerifyEmail:
    """Tests for AuthService.verify_email()"""

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_verify_email_success(self, mock_user_repo, mock_token_repo,
                                  mock_db, unverified_user):
        token_record = MagicMock()
        token_record.used = False
        token_record.expires_at = MagicMock()
        # Make the expiry comparison return False (not expired)
        token_record.expires_at.__lt__ = lambda self, other: False
        token_record.user_id = unverified_user.user_id

        mock_token_repo.get_by_token.return_value = token_record
        mock_user_repo.get_by_id.return_value = unverified_user

        data = MagicMock()
        data.token = "valid-token"

        result = AuthService.verify_email(mock_db, data)
        assert result["success"] is True
        assert "verified" in result["message"].lower()

    @patch("app.services.auth_service.TokenRepository")
    def test_verify_email_invalid_token(self, mock_token_repo, mock_db):
        mock_token_repo.get_by_token.return_value = None

        data = MagicMock()
        data.token = "bad-token"

        with pytest.raises(HTTPException) as exc:
            AuthService.verify_email(mock_db, data)
        assert exc.value.status_code == 400

    @patch("app.services.auth_service.TokenRepository")
    def test_verify_email_already_used(self, mock_token_repo, mock_db):
        token_record = MagicMock()
        token_record.used = True
        mock_token_repo.get_by_token.return_value = token_record

        data = MagicMock()
        data.token = "used-token"

        with pytest.raises(HTTPException) as exc:
            AuthService.verify_email(mock_db, data)
        assert exc.value.status_code == 400


class TestResendVerification:
    """Tests for AuthService.resend_verification()"""

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_resend_success(self, mock_user_repo, mock_token_repo,
                            mock_db, unverified_user):
        mock_user_repo.get_by_email.return_value = unverified_user
        mock_token_repo.count_recent_for_email.return_value = 0

        data = MagicMock()
        data.email = "test@example.com"

        result = AuthService.resend_verification(mock_db, data)
        assert result["success"] is True
        mock_token_repo.create.assert_called_once()

    @patch("app.services.auth_service.UserRepository")
    def test_resend_email_not_found(self, mock_user_repo, mock_db):
        mock_user_repo.get_by_email.return_value = None

        data = MagicMock()
        data.email = "noone@example.com"

        with pytest.raises(HTTPException) as exc:
            AuthService.resend_verification(mock_db, data)
        assert exc.value.status_code == 404

    @patch("app.services.auth_service.UserRepository")
    def test_resend_already_verified(self, mock_user_repo, mock_db,
                                     verified_user):
        mock_user_repo.get_by_email.return_value = verified_user

        data = MagicMock()
        data.email = "test@example.com"

        with pytest.raises(HTTPException) as exc:
            AuthService.resend_verification(mock_db, data)
        assert exc.value.status_code == 409

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_resend_rate_limited(self, mock_user_repo, mock_token_repo,
                                 mock_db, unverified_user):
        mock_user_repo.get_by_email.return_value = unverified_user
        mock_token_repo.count_recent_for_email.return_value = 3

        data = MagicMock()
        data.email = "test@example.com"

        with pytest.raises(HTTPException) as exc:
            AuthService.resend_verification(mock_db, data)
        assert exc.value.status_code == 429


class TestForgotPassword:
    """Tests for AuthService.forgot_password()"""

    @patch("app.services.auth_service.PasswordResetRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_forgot_password_existing_email(self, mock_user_repo,
                                            mock_reset_repo, mock_db,
                                            verified_user):
        mock_user_repo.get_by_email.return_value = verified_user
        mock_reset_repo.count_recent.return_value = 0

        data = MagicMock()
        data.email = "test@example.com"

        result = AuthService.forgot_password(mock_db, data)
        assert result["success"] is True
        # Should always return same message (anti-enumeration)
        assert "reset link" in result["message"].lower()

    @patch("app.services.auth_service.UserRepository")
    def test_forgot_password_nonexistent_email(self, mock_user_repo,
                                               mock_db):
        mock_user_repo.get_by_email.return_value = None

        data = MagicMock()
        data.email = "noone@example.com"

        result = AuthService.forgot_password(mock_db, data)
        # Should still return 200 (anti-enumeration)
        assert result["success"] is True

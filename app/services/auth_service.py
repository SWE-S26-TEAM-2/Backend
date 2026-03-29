"""
Service layer for authentication business logic.

Handles registration, login, email verification, and resend
verification logic. Delegates database operations to repositories
and token operations to the security module.
"""
import secrets
from datetime import datetime, timezone


from fastapi import HTTPException, status  # type: ignore
from google.auth.transport import requests as google_requests  # type: ignore
from google.oauth2 import id_token  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from jose import JWTError  # type: ignore

from app.core.security import (  # type: ignore
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User  # type: ignore
from app.repositories.token_repo import TokenRepository  # type: ignore
from app.repositories.user_repo import UserRepository  # type: ignore
from app.core.config import GOOGLE_CLIENT_ID  # type: ignore
from app.repositories.refresh_token_repo import RefreshTokenRepository  # type: ignore
from app.repositories.password_reset_repo import PasswordResetRepository  # type: ignore




class AuthService:
    """
    Business logic layer for all authentication operations.
    """

    @staticmethod
    def register_user(db: Session, data) -> dict:
        """
        Register a new user account and generate a verification token.

        Args:
            db (Session): The database session.
            data: The RegisterRequest schema with email, password, etc.

        Returns:
            dict: Success response with user_id, email, display_name.

        Raises:
            HTTPException: 409 if the email is already registered.
        """
        existing_user = UserRepository.get_by_email(db, data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        hashed = hash_password(data.password)

        new_user = User(
            email=data.email,
            password_hash=hashed,
            display_name=data.display_name,
            account_type=data.account_type or "listener",
        )

        UserRepository.create(db, new_user)

        # Generate an email verification token
        TokenRepository.create(db, new_user.user_id)

        return {
            "success": True,
            "message": (
                "Registration successful. "
                "Please check your email to verify your account."
            ),
            "data": {
                "user_id": str(new_user.user_id),
                "email": new_user.email,
                "display_name": new_user.display_name,
                "is_verified": new_user.is_verified,
            },
        }

    @staticmethod
    def verify_email(db: Session, data) -> dict:
        """
        Verify a user's email using the token sent to their inbox.

        Args:
            db (Session): The database session.
            data: The VerifyEmailRequest schema with the token string.

        Returns:
            dict: Success message confirming account verification.

        Raises:
            HTTPException: 400 if the token is invalid or already used.
            HTTPException: 410 if the token has expired.
        """
        token_record = TokenRepository.get_by_token(db, data.token)

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or malformed token",
            )

        if token_record.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token has already been used",
            )

        if token_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=(
                    "Token expired. "
                    "Use /auth/resend-verification to get a new one."
                ),
            )

        user = UserRepository.get_by_id(db, token_record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        UserRepository.update_verification_status(db, user, True)
        TokenRepository.mark_used(db, token_record)

        return {
            "success": True,
            "message": "Account verified. You can now log in.",
        }

    @staticmethod
    def resend_verification(db: Session, data) -> dict:
        """
        Resend a verification email to the user.

        Rate-limited to 3 active tokens per user to prevent abuse.

        Args:
            db (Session): The database session.
            data: The ResendVerificationRequest schema with email.

        Returns:
            dict: Success message confirming the email was resent.

        Raises:
            HTTPException: 404 if the email is not registered.
            HTTPException: 409 if the account is already verified.
            HTTPException: 429 if rate limit is exceeded.
        """
        user = UserRepository.get_by_email(db, data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found",
            )

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Account already verified",
            )

        active_count = TokenRepository.count_recent_for_email(
            db, user.user_id
        )
        if active_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )

        TokenRepository.create(db, user.user_id)

        return {
            "success": True,
            "message": (
                "Verification email resent. Please check your inbox."
            ),
        }

    @staticmethod
    def login_user(db: Session, data) -> dict:
        """
        Authenticate a user and issue JWT tokens.

        Args:
            db (Session): The database session.
            data: The LoginRequest schema with email and password.

        Returns:
            dict: Access token, refresh token, and user info.

        Raises:
            HTTPException: 401 if credentials are invalid.
            HTTPException: 403 if the account is not verified.
            HTTPException: 403 if the account is suspended.
        """
        user = UserRepository.get_by_email(db, data.email)

        if not user or not verify_password(
            data.password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not verified",
            )

        if user.is_suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended",
            )

        access_token = create_access_token(str(user.user_id))
        refresh_token = create_refresh_token(str(user.user_id))
        refresh_payload = decode_refresh_token(refresh_token)
        RefreshTokenRepository.create(db, refresh_payload["jti"], str(user.user_id))

        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "user_id": str(user.user_id),
                    "display_name": user.display_name,
                    "account_type": user.account_type,
                    "is_premium": user.is_premium,
                },
            },
        }
    
    @staticmethod
    def google_login(db: Session, data) -> dict:
        """
        Authenticate or auto-register a user via Google OAuth2 ID token.
 
        If no account exists for the Google email, one is created
        automatically with is_verified=True and a random unusable
        password hash. If an account already exists, the user is
        logged in directly.
 
        Args:
            db (Session): The database session.
            data: The GoogleLoginRequest schema containing google_token.
 
        Returns:
            dict: Access token, refresh token, token metadata, is_new_user
                  flag, and basic user info.
 
        Raises:
            HTTPException: 400 if the google_token field is missing or empty.
            HTTPException: 401 if the Google token is invalid or expired.
            HTTPException: 403 if the account is suspended.
            HTTPException: 503 if the Google OAuth service is unreachable.
        """
        if not data.google_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing or empty google_token.",
            )
 
        # Verify the ID token against Google's public keys.
        try:
            id_info = id_token.verify_oauth2_token(
                data.google_token,
                google_requests.Request(),
                GOOGLE_CLIENT_ID,
            )
        except ValueError:
            # verify_oauth2_token raises ValueError for invalid/expired tokens.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token invalid or expired.",
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth service unavailable.",
            )
 
        google_email: str = id_info.get("email")
        google_name: str = id_info.get("name", google_email.split("@")[0])
        google_picture: str = id_info.get("picture")
 
        existing_user = UserRepository.get_by_email(db, google_email)
        is_new_user = existing_user is None
 
        if is_new_user:
            # Auto-register the user.  Generate a random unusable password
            # so the NOT NULL column is satisfied, but the user can never
            # log in with it via the standard /auth/login route.
            unusable_hash = hash_password(secrets.token_urlsafe(32))
 
            new_user = User(
                email=google_email,
                password_hash=unusable_hash,
                display_name=google_name,
                account_type="listener",
                is_verified=True,
                profile_picture=google_picture,
            )
            UserRepository.create(db, new_user)
            user = new_user
        else:
            user = existing_user
 
        if user.is_suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended.",
            )
 
        access_token = create_access_token(str(user.user_id))
        refresh_token = create_refresh_token(str(user.user_id))
        refresh_payload = decode_refresh_token(refresh_token)
        RefreshTokenRepository.create(db, refresh_payload["jti"], str(user.user_id))
 
        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 900,
                "is_new_user": is_new_user,
                "user": {
                    "user_id": str(user.user_id),
                    "display_name": user.display_name,
                    "account_type": user.account_type,
                    "is_premium": user.is_premium,
                },
            },
        }
    

    @staticmethod
    def refresh_access_token(db: Session, data) -> dict:
        """
        Validate a refresh token, revoke it, and issue a new token pair.

        Implements refresh token rotation — the submitted token is
        invalidated immediately and a fresh pair is returned.

        Args:
            db (Session): The database session.
            data: The RefreshTokenRequest schema with the refresh token string.

        Returns:
            dict: New access token, refresh token, token type, and expires_in.

        Raises:
            HTTPException: 401 if the token is invalid, expired, or revoked.
            HTTPException: 403 if the account is suspended.
        """
        try:
            payload = decode_refresh_token(data.refresh_token)
            user_id: str = payload.get("sub")
            jti: str = payload.get("jti")
            if user_id is None or jti is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token invalid.",
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalid or expired.",
            )

        token_record = RefreshTokenRepository.get_by_jti(db, jti)
        if not token_record or token_record.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalid or already used.",
            )

        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalid.",
            )

        if user.is_suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended.",
            )

        RefreshTokenRepository.revoke(db, token_record)

        new_access_token = create_access_token(str(user.user_id))
        new_refresh_token = create_refresh_token(str(user.user_id))

        new_payload = decode_refresh_token(new_refresh_token)
        RefreshTokenRepository.create(db, new_payload["jti"], str(user.user_id))

        return {
            "success": True,
            "data": {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 900,
            },
        }

    @staticmethod
    def logout(db: Session, data, current_user) -> dict:
        """
        Invalidate the submitted refresh token and end the session.

        Revokes all active refresh tokens for the user so no other
        device sessions using old tokens can continue. The client
        must also discard the access token locally.

        Args:
            db (Session): The database session.
            data: The LogoutRequest schema with the refresh token string.
            current_user: The authenticated User from the JWT dependency.

        Returns:
            dict: Success message confirming logout.

        Raises:
            HTTPException: 400 if the refresh token is missing or invalid.
        """
        try:
            payload = decode_refresh_token(data.refresh_token)
            jti: str = payload.get("jti")
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token.",
            )

        RefreshTokenRepository.revoke_all_for_user(db, str(current_user.user_id))

        return {
            "success": True,
            "message": "Logged out successfully.",
        }

    @staticmethod
    def forgot_password(db: Session, data) -> dict:
        """
        Request a password reset for the given email address.

        Always returns 200 regardless of whether the email exists
        to prevent user enumeration attacks.

        Args:
            db (Session): The database session.
            data: The ForgotPasswordRequest schema with email.

        Returns:
            dict: Generic success message.

        Raises:
            HTTPException: 429 if rate limit exceeded (3 per hour).
        """
        generic_response = {
            "success": True,
            "message": (
                "If an account with that email exists, "
                "a reset link has been sent."
            ),
        }

        user = UserRepository.get_by_email(db, data.email)
        if not user:
            return generic_response

        active_count = PasswordResetRepository.count_recent(
            db, user.user_id
        )
        if active_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Max 3 reset requests per hour.",
            )

        PasswordResetRepository.create(db, user.user_id)

        return generic_response

    @staticmethod
    def reset_password(db: Session, data) -> dict:
        """
        Reset a user's password using a valid reset token.

        The token must be unused and not expired. On success, all
        active refresh tokens for the user are revoked.

        Args:
            db (Session): The database session.
            data: The ResetPasswordRequest schema with token and
                new_password.

        Returns:
            dict: Success message confirming password update.

        Raises:
            HTTPException: 400 if the token is invalid or already used.
            HTTPException: 410 if the token has expired.
        """
        token_record = PasswordResetRepository.get_by_token(
            db, data.token
        )

        if not token_record or token_record.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token invalid or already used.",
            )

        if token_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Token expired.",
            )

        user = UserRepository.get_by_id(db, token_record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token invalid or already used.",
            )

        new_hash = hash_password(data.new_password)
        UserRepository.update_password(db, user, new_hash)
        PasswordResetRepository.mark_used(db, token_record)
        RefreshTokenRepository.revoke_all_for_user(
            db, str(user.user_id)
        )

        return {
            "success": True,
            "message": (
                "Password updated successfully. "
                "All sessions have been terminated."
            ),
        }
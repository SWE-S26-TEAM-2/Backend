"""
Service layer for authentication business logic.

Handles registration, login, email verification, and resend
verification logic. Delegates database operations to repositories
and token operations to the security module.
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from jose import JWTError  # type: ignore

from app.core.security import (  # type: ignore
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models import user
from app.models.user import User  # type: ignore
from app.repositories.token_repo import TokenRepository  # type: ignore
from app.repositories.user_repo import UserRepository  # type: ignore


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
    def refresh_token(db: Session, data) -> dict:
        """
        Validate a refresh token and issue a new access/refresh token pair.

        Args:
            db (Session): The database session.
            data: The RefreshTokenRequest schema with the refresh token string.

        Returns:
            dict: New access token, refresh token, token type, and expires_in.

        Raises:
            HTTPException: 401 if the token is invalid, expired, or wrong type.
            HTTPException: 403 if the account is suspended.
        """
        try:
            payload = decode_refresh_token(data.refresh_token)
            user_id: str = payload.get("sub")
            if user_id is None:
                    raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalid.",
            )
        except JWTError:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired.",
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
            detail="Account suspended",
        )

        return {
        "success": True,
        "data": {
            "access_token": create_access_token(str(user.user_id)),
            "refresh_token": create_refresh_token(str(user.user_id)),
            "token_type": "bearer",
            "expires_in": 900,
        },
    }
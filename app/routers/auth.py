"""
Router for authentication endpoints (Module 1).

Handles registration, login, email verification,
and resend verification HTTP routes.
"""
from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.database.database import get_db  # type: ignore
from app.schemas.auth_schema import (  # type: ignore
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    GoogleLoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.core.dependencies import get_current_user  # type: ignore
from app.models.user import User  # type: ignore
from app.services.auth_service import AuthService  # type: ignore

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user account.

    Args:
        request (RegisterRequest): Registration data from the client.
        db (Session): Database session injected by FastAPI.

    Returns:
        dict: Success response with user data.
    """
    return AuthService.register_user(db, request)


@router.post("/verify-email")
def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    """
    Verify a user's email with a token.

    Args:
        request (VerifyEmailRequest): Token data from the email link.
        db (Session): Database session injected by FastAPI.

    Returns:
        dict: Success message confirming verification.
    """
    return AuthService.verify_email(db, request)


@router.post("/resend-verification")
def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """
    Resend a verification email to the user.

    Args:
        request (ResendVerificationRequest): Email to resend to.
        db (Session): Database session injected by FastAPI.

    Returns:
        dict: Success message confirming email was resent.
    """
    return AuthService.resend_verification(db, request)


@router.post("/login")
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login with email and password to receive JWT tokens.

    Args:
        request (LoginRequest): Login credentials from the client.
        db (Session): Database session injected by FastAPI.

    Returns:
        dict: Access token, refresh token, and user info.
    """
    return AuthService.login_user(db, request)

@router.post("/google")
def google_login(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate or auto-register a user via Google OAuth2.
 
    Args:
        request (GoogleLoginRequest): Google ID token from the client SDK.
        db (Session): Database session injected by FastAPI.
 
    Returns:
        dict: Access token, refresh token, is_new_user flag, and user info.
    """
    return AuthService.google_login(db, request)
@router.post("/refresh")
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Issue a new access and refresh token using a valid refresh token.

    Args:
        request (RefreshTokenRequest): The current refresh token.
        db (Session): Database session injected by FastAPI.

    Returns:
        dict: New access token, refresh token, token type, and expiry.
    """
    return AuthService.refresh_access_token(db, request)

@router.post("/logout")
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logout the current user and invalidate their session.

    Args:
        request (LogoutRequest): The refresh token to invalidate.
        db (Session): Database session injected by FastAPI.
        current_user (User): The authenticated user from JWT dependency.

    Returns:
        dict: Success message confirming logout.
    """
    return AuthService.logout(db, request, current_user)


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset link for the given email.

    Always returns 200 regardless of whether the email is registered
    to prevent user enumeration.

    Args:
        request (ForgotPasswordRequest): Email to send reset link to.
        db (Session): Database session injected by FastAPI.

    Returns:
        dict: Generic success message.
    """
    return AuthService.forgot_password(db, request)


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Reset a user's password using a valid reset token.

    Args:
        request (ResetPasswordRequest): Token and new password.
        db (Session): Database session injected by FastAPI.

    Returns:
        dict: Success message confirming password update.
    """
    return AuthService.reset_password(db, request)
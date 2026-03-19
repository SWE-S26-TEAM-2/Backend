"""
Router for authentication endpoints (Module 1).

Handles registration, login, email verification,
and resend verification HTTP routes.
"""
from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.database.database import get_db  # type: ignore
from app.schemas.auth_schema import (  # type: ignore
    LoginRequest,
    RegisterRequest,
    ResendVerificationRequest,
    VerifyEmailRequest,
)
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
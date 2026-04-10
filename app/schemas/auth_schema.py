"""
Pydantic schemas for authentication request/response validation.

Defines the data contracts for registration, login, email verification,
resend verification, and password management endpoints.
"""
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator  # type: ignore


class RegisterRequest(BaseModel):
    """
    Schema for user registration request.

    Args:
        email (EmailStr): Valid email address, must be unique.
        password (str): Minimum 8 characters.
        display_name (str): Public display name.
        account_type (str, optional): 'artist' or 'listener'. Defaults to 'listener'.
    """

    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str
    account_type: Optional[str] = "listener"


class LoginRequest(BaseModel):
    """
    Schema for user login request.

    Args:
        email (EmailStr): Registered email address.
        password (str): Account password.
    """

    email: EmailStr
    password: str


class VerifyEmailRequest(BaseModel):
    """
    Schema for email verification request.

    Args:
        token (str): Verification token from the email link.
    """

    token: str


class ResendVerificationRequest(BaseModel):
    """
    Schema for resending the verification email.

    Args:
        email (EmailStr): The registered email address to resend to.
    """

    email: EmailStr

class RefreshTokenRequest(BaseModel):
    """
    Schema for refresh token request.

    Args:
        refresh_token (str): The current valid refresh token.
    """

    refresh_token: str


class GoogleLoginRequest(BaseModel):
    """
    Schema for Google OAuth2 social login request.
 
    Args:
        google_token (str): The Google ID token returned by the
            client-side Google Sign-In SDK.
    """
 
    google_token: str


class LogoutRequest(BaseModel):
    """
    Schema for logout request.

    Args:
        refresh_token (str): The refresh token to invalidate server-side.
    """

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """
    Schema for requesting a password reset link.

    Args:
        email (EmailStr): Email address of the account.
    """

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """
    Schema for resetting a password with a reset token.

    Args:
        token (str): Password reset token from the email link.
        new_password (str): New password. Min 8 chars, 1 uppercase,
            1 number.
    """

    token: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        """
        Validate that the password has at least one uppercase letter
        and at least one digit.

        Args:
            value (str): The new password string.

        Returns:
            str: The validated password.

        Raises:
            ValueError: If the password is missing uppercase or digit.
        """
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[0-9]", value):
            raise ValueError(
                "Password must contain at least one digit."
            )
        return value
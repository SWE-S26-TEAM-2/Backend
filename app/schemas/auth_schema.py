"""
Pydantic schemas for authentication request/response validation.

Defines the data contracts for registration, login, email verification,
and resend verification endpoints.
"""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field  # type: ignore


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
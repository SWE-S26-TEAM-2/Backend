"""
Pydantic schemas for user profile request/response validation.

Defines the data contracts for profile retrieval, updates,
and privacy toggle endpoints.
"""
from typing import Optional

from pydantic import BaseModel, Field  # type: ignore


class UpdateProfileRequest(BaseModel):
    """
    Schema for partial profile update.

    All fields are optional — only provided fields are updated.

    Args:
        display_name (str, optional): New display name.
        bio (str, optional): Profile bio. Max 500 characters.
        location (str, optional): Location string.
        account_type (str, optional): 'artist' or 'listener'.
    """

    display_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = None
    account_type: Optional[str] = None


class UpdatePrivacyRequest(BaseModel):
    """
    Schema for toggling profile visibility.

    Args:
        is_private (bool): True for private, False for public.
    """

    is_private: bool

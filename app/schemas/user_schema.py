"""
Pydantic schemas for user profile request/response validation.

Defines the data contracts for profile retrieval, updates,
and privacy toggle endpoints.
"""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator  # type: ignore


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=20)
    display_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = None
    account_type: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if value is None:
            return value
        if not re.match(r"^[a-zA-Z0-9_.\-]+$", value):
            raise ValueError(
                "Username may only contain letters, numbers, "
                "underscores, dots, and hyphens."
            )
        return value.lower()


class UpdatePrivacyRequest(BaseModel):
    """
    Schema for toggling profile visibility.

    Args:
        is_private (bool): True for private, False for public.
    """

    is_private: bool

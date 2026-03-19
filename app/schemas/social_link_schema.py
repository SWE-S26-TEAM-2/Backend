"""
Pydantic schemas for social link request/response validation.

Defines the data contracts for social link retrieval and updates.
"""
from typing import List

from pydantic import BaseModel, field_validator  # type: ignore


ALLOWED_PLATFORMS = [
    "instagram",
    "twitter",
    "facebook",
    "youtube",
    "website",
]


class SocialLinkItem(BaseModel):
    """
    Schema for a single social link entry.

    Args:
        platform (str): Platform name (instagram, twitter, etc.).
        url (str): Full URL starting with https://.
    """

    platform: str
    url: str

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, value: str) -> str:
        """
        Validate that the platform is one of the allowed values.

        Args:
            value (str): The platform string to validate.

        Returns:
            str: The validated platform string.

        Raises:
            ValueError: If the platform is not in the allowed list.
        """
        if value not in ALLOWED_PLATFORMS:
            raise ValueError(
                f"Invalid platform. Accepted: {ALLOWED_PLATFORMS}"
            )
        return value

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """
        Validate that the URL starts with https://.

        Args:
            value (str): The URL string to validate.

        Returns:
            str: The validated URL string.

        Raises:
            ValueError: If the URL does not start with https://.
        """
        if not value.startswith("https://"):
            raise ValueError("URL must start with https://")
        return value


class UpdateSocialLinksRequest(BaseModel):
    """
    Schema for replacing all social links.

    Args:
        social_links (List[SocialLinkItem]): Complete list of links.
            Max 5 links. Send empty list to clear all links.
    """

    social_links: List[SocialLinkItem]

    @field_validator("social_links")
    @classmethod
    def validate_max_links(
        cls, value: List[SocialLinkItem],
    ) -> List[SocialLinkItem]:
        """
        Validate that no more than 5 social links are provided.

        Args:
            value (List[SocialLinkItem]): The list of social links.

        Returns:
            List[SocialLinkItem]: The validated list.

        Raises:
            ValueError: If more than 5 links are provided.
        """
        if len(value) > 5:
            raise ValueError("Maximum 5 social links are allowed")
        return value

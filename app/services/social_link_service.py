"""
Service layer for social link business logic.

Handles retrieval and full-replacement updates of
external social profile links for a user.
"""
from sqlalchemy.orm import Session  # type: ignore

from app.models.user import User  # type: ignore
from app.repositories.social_link_repo import (  # type: ignore
    SocialLinkRepository,
)


class SocialLinkService:
    """
    Business logic layer for social link operations.
    """

    @staticmethod
    def get_social_links(
        db: Session, current_user: User
    ) -> dict:
        """
        Get all social links for the authenticated user.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated user object.

        Returns:
            dict: List of social link objects.
        """
        links = SocialLinkRepository.get_by_user_id(
            db, current_user.user_id
        )

        return {
            "success": True,
            "data": {
                "social_links": [
                    {"platform": l.platform, "url": l.url}
                    for l in links
                ],
            },
        }

    @staticmethod
    def update_social_links(
        db: Session, current_user: User, data
    ) -> dict:
        """
        Replace all social links for the authenticated user.

        Deletes existing links and creates new ones from the request.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated user object.
            data: UpdateSocialLinksRequest schema.

        Returns:
            dict: Updated list of social link objects.
        """
        SocialLinkRepository.delete_by_user_id(
            db, current_user.user_id
        )
        SocialLinkRepository.create_many(
            db, current_user.user_id, data.social_links
        )

        # Re-fetch to get the DB-generated IDs
        updated = SocialLinkRepository.get_by_user_id(
            db, current_user.user_id
        )

        return {
            "success": True,
            "message": "Social links updated successfully.",
            "data": {
                "social_links": [
                    {"platform": l.platform, "url": l.url}
                    for l in updated
                ],
            },
        }

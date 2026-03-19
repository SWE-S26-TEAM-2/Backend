"""
Repository for SocialLink database operations.

Handles retrieval, deletion, and creation of social links
for a given user.
"""
from typing import List

from sqlalchemy.orm import Session  # type: ignore

from app.models.social_link import SocialLink  # type: ignore


class SocialLinkRepository:
    """
    Database interaction layer for the SocialLink model.
    """

    @staticmethod
    def get_by_user_id(
        db: Session, user_id
    ) -> List[SocialLink]:
        """
        Get all social links for a user.

        Args:
            db (Session): The database session.
            user_id: The UUID of the user.

        Returns:
            List[SocialLink]: All social link records for the user.
        """
        return (
            db.query(SocialLink)
            .filter(SocialLink.user_id == user_id)
            .all()
        )

    @staticmethod
    def delete_by_user_id(db: Session, user_id) -> None:
        """
        Delete all social links for a user.

        Args:
            db (Session): The database session.
            user_id: The UUID of the user.

        Returns:
            None
        """
        db.query(SocialLink).filter(
            SocialLink.user_id == user_id
        ).delete()

    @staticmethod
    def create_many(
        db: Session, user_id, links: list
    ) -> List[SocialLink]:
        """
        Create multiple social links for a user.

        Args:
            db (Session): The database session.
            user_id: The UUID of the user.
            links (list): List of SocialLinkItem schemas.

        Returns:
            List[SocialLink]: The created social link records.
        """
        new_links = []
        for link in links:
            new_link = SocialLink(
                user_id=user_id,
                platform=link.platform,
                url=link.url,
            )
            db.add(new_link)
            new_links.append(new_link)
        db.commit()
        return new_links

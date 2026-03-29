"""
Repository for email verification token database operations.

Handles creation, lookup, and status updates for verification tokens.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session  # type: ignore

from app.models.email_verification import EmailVerification  # type: ignore


class TokenRepository:
    """
    Database interaction layer for EmailVerification tokens.
    """

    @staticmethod
    def create(db: Session, user_id: str) -> EmailVerification:
        """
        Create a new email verification token for a user.

        Args:
            db (Session): The database session.
            user_id (str): The UUID of the user.

        Returns:
            EmailVerification: The created token record.
        """
        token = EmailVerification(
            user_id=user_id,
            token=EmailVerification.generate_token(),
            expires_at=EmailVerification.default_expiry(),
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def get_by_token(db: Session, token: str):
        """
        Look up a verification token record by its token string.

        Args:
            db (Session): The database session.
            token (str): The verification token string.

        Returns:
            EmailVerification or None: The token record if found.
        """
        return (
            db.query(EmailVerification)
            .filter(EmailVerification.token == token)
            .first()
        )

    @staticmethod
    def mark_used(db: Session, token_record: EmailVerification) -> None:
        """
        Mark a verification token as used so it cannot be reused.

        Args:
            db (Session): The database session.
            token_record (EmailVerification): The token record to mark.

        Returns:
            None
        """
        token_record.used = True
        db.commit()

    @staticmethod
    def count_recent_for_email(db: Session, user_id: str) -> int:
        """
        Count how many unused tokens exist for a user (rate limiting).

        Args:
            db (Session): The database session.
            user_id (str): The UUID of the user.

        Returns:
            int: The number of active (unused, non-expired) tokens.
        """
        now = datetime.now(timezone.utc)
        return (
            db.query(EmailVerification)
            .filter(
                EmailVerification.user_id == user_id,
                EmailVerification.used.is_(False),
                EmailVerification.expires_at > now,
            )
            .count()
        )

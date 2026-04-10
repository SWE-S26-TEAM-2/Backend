"""
Repository for password reset token database operations.

Handles creation, lookup, and status updates for password reset tokens.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session  # type: ignore

from app.models.password_reset import PasswordReset  # type: ignore


class PasswordResetRepository:
    """
    Database interaction layer for PasswordReset tokens.
    """

    @staticmethod
    def create(db: Session, user_id: str) -> PasswordReset:
        """
        Create a new password reset token for a user.

        Args:
            db (Session): The database session.
            user_id (str): The UUID of the user.

        Returns:
            PasswordReset: The created token record.
        """
        token = PasswordReset(
            user_id=user_id,
            token=PasswordReset.generate_token(),
            expires_at=PasswordReset.default_expiry(),
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def get_by_token(db: Session, token: str):
        """
        Look up a password reset token record by its token string.

        Args:
            db (Session): The database session.
            token (str): The reset token string.

        Returns:
            PasswordReset or None: The token record if found.
        """
        return (
            db.query(PasswordReset)
            .filter(PasswordReset.token == token)
            .first()
        )

    @staticmethod
    def mark_used(db: Session, token_record: PasswordReset) -> None:
        """
        Mark a password reset token as used so it cannot be reused.

        Args:
            db (Session): The database session.
            token_record (PasswordReset): The token record to mark.

        Returns:
            None
        """
        token_record.used = True
        db.commit()

    @staticmethod
    def count_recent(db: Session, user_id: str) -> int:
        """
        Count how many unused, non-expired reset tokens exist for a user.

        Used for rate limiting — max 3 active reset requests per hour.

        Args:
            db (Session): The database session.
            user_id (str): The UUID of the user.

        Returns:
            int: The number of active (unused, non-expired) reset tokens.
        """
        now = datetime.now(timezone.utc)
        return (
            db.query(PasswordReset)
            .filter(
                PasswordReset.user_id == user_id,
                PasswordReset.used.is_(False),
                PasswordReset.expires_at > now,
            )
            .count()
        )

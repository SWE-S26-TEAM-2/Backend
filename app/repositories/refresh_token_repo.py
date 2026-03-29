"""
Repository for refresh token database operations.

Handles creation, lookup, and revocation of refresh tokens.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session  # type: ignore

from app.models.refresh_token import RefreshToken  # type: ignore


class RefreshTokenRepository:
    """
    Database interaction layer for RefreshToken records.
    """

    @staticmethod
    def create(db: Session, jti: str, user_id: str) -> RefreshToken:
        """
        Store a newly issued refresh token.

        Args:
            db (Session): The database session.
            jti (str): The unique token identifier from the JWT payload.
            user_id (str): The UUID of the user as a string.

        Returns:
            RefreshToken: The created token record.
        """
        record = RefreshToken(
            jti=uuid.UUID(jti),
            user_id=uuid.UUID(str(user_id)),
            expires_at=RefreshToken.default_expiry(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_by_jti(db: Session, jti: str):
        """
        Look up a refresh token record by its jti.

        Args:
            db (Session): The database session.
            jti (str): The JWT ID string to search for.

        Returns:
            RefreshToken or None: The record if found.
        """
        return (
            db.query(RefreshToken)
            .filter(RefreshToken.jti == uuid.UUID(jti))
            .first()
        )

    @staticmethod
    def revoke(db: Session, token_record: RefreshToken) -> None:
        """
        Mark a refresh token as revoked.

        Args:
            db (Session): The database session.
            token_record (RefreshToken): The token record to revoke.

        Returns:
            None
        """
        token_record.revoked = True
        db.commit()

    @staticmethod
    def revoke_all_for_user(db: Session, user_id: str) -> None:
        """
        Revoke all active refresh tokens for a user (used on logout).

        Args:
            db (Session): The database session.
            user_id (str): The UUID of the user as a string.

        Returns:
            None
        """
        now = datetime.now(timezone.utc)
        (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == uuid.UUID(str(user_id)),
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > now,
            )
            .update({"revoked": True})
        )
        db.commit()
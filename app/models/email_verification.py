"""
SQLAlchemy model for email verification tokens.

Stores one-time-use tokens sent to users after registration.
Tokens expire after 24 hours and can only be used once.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import (  # type: ignore
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class EmailVerification(Base):
    """
    Database model for email verification tokens.

    Each token is tied to a user, expires in 24 hours,
    and is marked as used after successful verification.
    """

    __tablename__ = "email_verifications"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)

    @staticmethod
    def generate_token() -> str:
        """
        Generate a unique verification token string.

        Returns:
            str: A UUID4 string to use as a verification token.
        """
        return str(uuid.uuid4())

    @staticmethod
    def default_expiry() -> datetime:
        """
        Calculate the default expiry time (24 hours from now).

        Returns:
            datetime: The expiration timestamp.
        """
        return datetime.now(timezone.utc) + timedelta(hours=24)

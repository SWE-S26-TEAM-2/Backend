"""
SQLAlchemy model for password reset tokens.

Stores one-time-use tokens sent to users when they request a password
reset. Tokens expire after 1 hour and can only be used once.
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


class PasswordReset(Base):
    """
    Database model for password reset tokens.

    Each token is tied to a user, expires in 1 hour,
    and is marked as used after a successful password reset.
    """

    __tablename__ = "password_resets"

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
        Generate a unique password reset token string.

        Returns:
            str: A UUID4 string to use as a reset token.
        """
        return str(uuid.uuid4())

    @staticmethod
    def default_expiry() -> datetime:
        """
        Calculate the default expiry time (1 hour from now).

        Returns:
            datetime: The expiration timestamp.
        """
        return datetime.now(timezone.utc) + timedelta(hours=1)

"""
SQLAlchemy model for refresh token storage.

Stores issued refresh tokens by jti for rotation and revocation.
Tokens are invalidated on use (rotation) or on logout.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class RefreshToken(Base):
    """
    Database model for issued refresh tokens.

    Each record tracks a single refresh token by its jti.
    Tokens are marked as revoked on use or logout.
    """

    __tablename__ = "refresh_tokens"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    jti = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)

    @staticmethod
    def default_expiry() -> datetime:
        """
        Calculate the default expiry (7 days from now).

        Returns:
            datetime: The expiration timestamp.
        """
        return datetime.now(timezone.utc) + timedelta(days=7)
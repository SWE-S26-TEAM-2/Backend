"""
SQLAlchemy model for the Follow relationship.

Represents a directional follow between two users.
follower_id  → the user who clicked "Follow"
following_id → the user being followed
"""

import uuid

from sqlalchemy import Column, TIMESTAMP, ForeignKey, text  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Follow(Base):
    __tablename__ = "follows"
    __allow_unmapped__ = True

    follow_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    following_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

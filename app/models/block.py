"""
SQLAlchemy model for the Block relationship.

Represents a block action from one user against another.
blocker_id → the user who initiated the block
blocked_id → the user being blocked
"""

import uuid

from sqlalchemy import Column, TIMESTAMP, ForeignKey, text  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Block(Base):
    __tablename__ = "blocks"
    __allow_unmapped__ = True

    block_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    blocked_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

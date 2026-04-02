"""
SQLAlchemy model for a 1-to-1 Conversation.

A conversation is a private channel between exactly two users.
user1_id and user2_id are stored in a consistent sorted order
at creation time so that (A,B) and (B,A) always resolve to
the same row — preventing duplicate conversations.
"""

import uuid

from sqlalchemy import Column, TIMESTAMP, ForeignKey, text  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Conversation(Base):
    __tablename__ = "conversations"
    __allow_unmapped__ = True

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Sorted at service layer: smaller UUID always goes in user1_id
    user1_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    user2_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

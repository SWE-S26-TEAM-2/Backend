"""
SQLAlchemy model for a Message inside a Conversation.

Supports plain text messages as well as optional
track and playlist sharing via nullable foreign keys.
receiver_id and is_read enable read-receipt tracking.
"""

from modulefinder import test
import uuid

from sqlalchemy import (  # type: ignore
    Boolean,
    Column,
    ForeignKey,
    String,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Message(Base):
    __tablename__ = "messages"
    __allow_unmapped__ = True

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    receiver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    content = Column(
        String, nullable=True
    )  # nullable — message may be a track/playlist share with no text
    track_id = Column(
        UUID(as_uuid=True),
        nullable=True,  # optional — only set when sharing a track
    )
    playlist_id = Column(
        UUID(as_uuid=True),
        nullable=True,  # optional — only set when sharing a playlist
    )
    is_read = Column(Boolean, server_default="false", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
# test
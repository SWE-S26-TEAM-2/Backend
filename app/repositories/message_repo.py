"""
Repository for Message database operations.

All raw queries for the messages table live here.
"""

from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session  # type: ignore

from app.models.message import Message  # type: ignore


class MessageRepository:

    @staticmethod
    def get_by_conversation(db: Session, conversation_id):
        """
        Retrieve all messages in a conversation, oldest first.

        Args:
            db (Session): The database session.
            conversation_id: UUID of the conversation.

        Returns:
            list[Message]: All messages ordered by created_at ASC.
        """
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    @staticmethod
    def create(
        db: Session,
        conversation_id,
        sender_id,
        receiver_id,
        content: Optional[str],
        track_id: Optional[UUID],
        playlist_id: Optional[UUID],
    ) -> Message:
        """
        Insert a new message into a conversation.

        Args:
            db (Session): The database session.
            conversation_id: UUID of the parent conversation.
            sender_id: UUID of the user sending the message.
            receiver_id: UUID of the user receiving the message.
            content (str, optional): The message text.
            track_id (UUID, optional): Shared track UUID.
            playlist_id (UUID, optional): Shared playlist UUID.

        Returns:
            Message: The newly created message record.
        """
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            track_id=track_id,
            playlist_id=playlist_id,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

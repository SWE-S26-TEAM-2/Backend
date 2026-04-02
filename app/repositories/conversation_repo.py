"""
Repository for Conversation database operations.

All raw queries for the conversations table live here.
The service layer calls these — never queries the DB directly.
"""

from sqlalchemy.orm import Session  # type: ignore

from app.models.conversation import Conversation  # type: ignore


class ConversationRepository:

    @staticmethod
    def get_by_participants(db: Session, user1_id, user2_id):
        """
        Find an existing conversation between two users.

        IDs must already be sorted before calling this method.
        Sorting is done once in the service layer on creation.

        Args:
            db (Session): The database session.
            user1_id: The smaller of the two UUIDs.
            user2_id: The larger of the two UUIDs.

        Returns:
            Conversation or None: Existing conversation if found.
        """
        return (
            db.query(Conversation)
            .filter(
                Conversation.user1_id == user1_id,
                Conversation.user2_id == user2_id,
            )
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, conversation_id):
        """
        Find a conversation by its primary key UUID.

        Args:
            db (Session): The database session.
            conversation_id: UUID of the conversation.

        Returns:
            Conversation or None.
        """
        return (
            db.query(Conversation)
            .filter(Conversation.conversation_id == conversation_id)
            .first()
        )

    @staticmethod
    def create(db: Session, user1_id, user2_id) -> Conversation:
        """
        Insert a new conversation record.

        Args:
            db (Session): The database session.
            user1_id: The smaller UUID (pre-sorted by service layer).
            user2_id: The larger UUID (pre-sorted by service layer).

        Returns:
            Conversation: The newly created conversation.
        """
        conversation = Conversation(
            user1_id=user1_id,
            user2_id=user2_id,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

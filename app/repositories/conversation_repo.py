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

    @staticmethod
    def get_all_by_user(db: Session, user_id) -> list:
        """
        Retrieve all conversations where the user is user1 or user2.

        Args:
            db (Session): The database session.
            user_id: UUID of the requesting user.

        Returns:
            list[Conversation]: All conversations for this user.
        """
        from app.models.conversation import Conversation

        # Cast to string for consistent UUID comparison across SQLite/PostgreSQL
        user_id_str = str(user_id)

        return (
            db.query(Conversation)
            .filter(
                (Conversation.user1_id == user_id_str)
                | (Conversation.user2_id == user_id_str)
            )
            .order_by(Conversation.created_at.desc())
            .all()
        )

    @staticmethod
    def delete(db: Session, conversation: Conversation) -> None:
        """
        Delete a conversation record and cascade-delete its messages.

        Cascade deletion of messages is handled at the DB level
        via the ForeignKey ondelete='CASCADE' on the messages table.

        Args:
            db (Session): The database session.
            conversation (Conversation): The conversation to delete.
        """
        db.delete(conversation)
        db.commit()

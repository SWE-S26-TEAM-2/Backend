"""
Service layer for messaging business logic.

Handles conversation creation (idempotent), message retrieval,
message sending, read receipts, conversation listing and deletion.
"""

from uuid import UUID

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.conversation import Conversation  # type: ignore
from app.models.message import Message  # type: ignore
from app.models.user import User  # type: ignore
from app.repositories.conversation_repo import ConversationRepository  # type: ignore
from app.repositories.message_repo import MessageRepository  # type: ignore
from app.repositories.user_repo import UserRepository  # type: ignore
from app.schemas.conversation_schema import (  # type: ignore
    CreateConversationRequest,
    SendMessageRequest,
)


class MessagingService:

    @staticmethod
    def create_or_get_conversation(
        db: Session,
        current_user: User,
        data: CreateConversationRequest,
    ) -> dict:
        """
        Create a new 1-to-1 conversation or return the existing one.
        """
        try:
            participant_uuid = UUID(str(data.participant_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid participant_id — must be a valid UUID.",
            )

        if str(current_user.user_id) == str(participant_uuid):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot start a conversation with yourself.",
            )

        participant = UserRepository.get_by_id(db, participant_uuid)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid participant — user does not exist.",
            )

        ids = sorted([str(current_user.user_id), str(participant_uuid)])
        user1 = UUID(ids[0])
        user2 = UUID(ids[1])

        existing = ConversationRepository.get_by_participants(db, user1, user2)
        if existing:
            return {
                "success": True,
                "data": {"conversation_id": str(existing.conversation_id)},
            }

        conversation = ConversationRepository.create(db, user1, user2)

        return {
            "success": True,
            "data": {"conversation_id": str(conversation.conversation_id)},
        }

    @staticmethod
    def get_messages(
        db: Session,
        current_user: User,
        conversation_id,
    ) -> dict:
        """
        Retrieve all messages in a conversation.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        is_participant = str(current_user.user_id) in [
            str(conversation.user1_id),
            str(conversation.user2_id),
        ]
        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation.",
            )

        messages = MessageRepository.get_by_conversation(db, conversation_id)

        return {
            "success": True,
            "data": [
                {
                    "id": str(msg.message_id),
                    "sender_id": str(msg.sender_id),
                    "receiver_id": str(msg.receiver_id),
                    "content": msg.content,
                    "track_id": (str(msg.track_id) if msg.track_id else None),
                    "playlist_id": (str(msg.playlist_id) if msg.playlist_id else None),
                    "is_read": msg.is_read,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ],
        }

    @staticmethod
    def send_message(
        db: Session,
        current_user: User,
        conversation_id,
        data: SendMessageRequest,
    ) -> dict:
        """
        Send a message inside an existing conversation.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        is_participant = str(current_user.user_id) in [
            str(conversation.user1_id),
            str(conversation.user2_id),
        ]
        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation.",
            )

        receiver_id = (
            conversation.user2_id
            if str(current_user.user_id) == str(conversation.user1_id)
            else conversation.user1_id
        )

        message = MessageRepository.create(
            db,
            conversation_id=conversation_id,
            sender_id=current_user.user_id,
            receiver_id=receiver_id,
            content=data.content,
            track_id=data.track_id,
            playlist_id=data.playlist_id,
        )

        return {
            "success": True,
            "data": {
                "id": str(message.message_id),
                "sender_id": str(message.sender_id),
                "receiver_id": str(message.receiver_id),
                "content": message.content,
                "track_id": (str(message.track_id) if message.track_id else None),
                "playlist_id": (
                    str(message.playlist_id) if message.playlist_id else None
                ),
                "is_read": message.is_read,
                "created_at": message.created_at,
            },
        }

    @staticmethod
    def mark_message_as_read(
        db: Session,
        current_user: User,
        conversation_id,
        message_id,
    ) -> dict:
        """
        Mark a specific message as read.

        Casts all UUIDs to str before every comparison to avoid
        any SQLAlchemy / PostgreSQL UUID type mismatch that causes
        the query to silently return None even when the row exists.
        """
        # ── Step 1: Conversation must exist ───────────────
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        # ── Step 2: Requester must be a participant ────────
        is_participant = str(current_user.user_id) in [
            str(conversation.user1_id),
            str(conversation.user2_id),
        ]
        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation.",
            )

        # ── Step 3: Look up message by message_id only ────
        # Do NOT filter by conversation_id in the same query —
        # check conversation ownership separately via str comparison
        # to avoid UUID type coercion bugs.
        message = (
            db.query(Message).filter(Message.message_id == str(message_id)).first()
        )

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found.",
            )

        # ── Step 4: Confirm message belongs to this conversation
        if str(message.conversation_id) != str(conversation_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message does not belong to this conversation.",
            )

        # ── Step 5: Only the receiver can mark it as read ─
        if str(message.receiver_id) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the message receiver can mark it as read.",
            )

        # ── Step 6: Idempotent — already read is fine ─────
        if message.is_read:
            return {
                "success": True,
                "message": "Message was already marked as read.",
                "data": {
                    "message_id": str(message.message_id),
                    "is_read": True,
                },
            }

        # ── Step 7: Flip the flag ──────────────────────────
        message.is_read = True
        db.commit()
        db.refresh(message)

        return {
            "success": True,
            "message": "Message marked as read.",
            "data": {
                "message_id": str(message.message_id),
                "is_read": message.is_read,
            },
        }

    @staticmethod
    def get_user_conversations(
        db: Session,
        current_user: User,
    ) -> dict:
        """
        Get all conversations for the authenticated user.
        """
        conversations = ConversationRepository.get_all_by_user(db, current_user.user_id)

        result = []
        for conv in conversations:
            user1 = UserRepository.get_by_id(db, conv.user1_id)
            user2 = UserRepository.get_by_id(db, conv.user2_id)

            result.append(
                {
                    "conversation_id": str(conv.conversation_id),
                    "created_at": conv.created_at,
                    "participants": [
                        {
                            "user_id": str(user1.user_id),
                            "display_name": user1.display_name,
                            "profile_picture": user1.profile_picture,
                        },
                        {
                            "user_id": str(user2.user_id),
                            "display_name": user2.display_name,
                            "profile_picture": user2.profile_picture,
                        },
                    ],
                }
            )

        return {
            "success": True,
            "data": result,
        }

    @staticmethod
    def delete_conversation(
        db: Session,
        current_user: User,
        conversation_id,
    ) -> dict:
        """
        Delete a conversation and all its messages.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )

        is_participant = str(current_user.user_id) in [
            str(conversation.user1_id),
            str(conversation.user2_id),
        ]
        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this conversation.",
            )

        ConversationRepository.delete(db, conversation)

        return {
            "success": True,
            "message": "Conversation deleted successfully.",
        }

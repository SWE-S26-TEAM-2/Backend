"""
Router for messaging endpoints (Module 9).

All endpoints require Bearer JWT authentication.
Prefix: /conversations

Endpoints:
  POST   /conversations                                    — Create or get conversation
  GET    /conversations                                    — Get all user conversations
  DELETE /conversations/{conversation_id}                   — Delete a conversation
  GET    /conversations/{conversation_id}/messages          — Get all messages
  POST   /conversations/{conversation_id}/messages          — Send a message
  PATCH  /conversations/{conversation_id}/messages/{message_id}/read — Mark as read
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user  # type: ignore
from app.database.database import get_db  # type: ignore
from app.models.user import User  # type: ignore
from app.schemas.conversation_schema import (  # type: ignore
    CreateConversationRequest,
    SendMessageRequest,
)
from app.services.messaging_service import MessagingService  # type: ignore

router = APIRouter(prefix="/conversations", tags=["Messaging"])


# ── Conversation Endpoints ─────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
def create_or_get_conversation(
    data: CreateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new 1-to-1 conversation or return an existing one.

    If a conversation already exists between the authenticated user
    and the given participant, the existing record is returned.

    Args:
        data (CreateConversationRequest): Body with participant_id.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: conversation_id of the new or existing conversation.
    """
    return MessagingService.create_or_get_conversation(db, current_user, data)


@router.get("", status_code=status.HTTP_200_OK)
def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all conversations for the authenticated user.

    Returns each conversation with both participants'
    user_id, display_name, and profile_picture.
    Ordered newest conversation first.

    Args:
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: List of conversations with participant details.
    """
    return MessagingService.get_user_conversations(db, current_user)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
)
def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a conversation and all its messages permanently.

    Only a participant of the conversation can delete it.
    All messages are removed via cascade delete.

    Args:
        conversation_id (UUID): Conversation UUID from the URL path.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Success confirmation message.
    """
    return MessagingService.delete_conversation(db, current_user, conversation_id)


# ── Message Endpoints ──────────────────────────────────


@router.get(
    "/{conversation_id}/messages",
    status_code=status.HTTP_200_OK,
)
def get_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all messages in a conversation, ordered oldest-first.

    Only the two participants of the conversation can access this.

    Args:
        conversation_id (UUID): Conversation UUID from the URL path.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: List of message objects including track/playlist fields.
    """
    return MessagingService.get_messages(db, current_user, conversation_id)


@router.post(
    "/{conversation_id}/messages",
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    conversation_id: UUID,
    data: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message inside an existing conversation.

    Supports plain text, track sharing, playlist sharing,
    or any combination. Only participants can send messages.

    Args:
        conversation_id (UUID): Conversation UUID from the URL path.
        data (SendMessageRequest): Body with content/track_id/playlist_id.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: The newly created message with all fields.
    """
    return MessagingService.send_message(db, current_user, conversation_id, data)


@router.patch(
    "/{conversation_id}/messages/{message_id}/read",
    status_code=status.HTTP_200_OK,
)
def mark_message_as_read(
    conversation_id: UUID,
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a specific message as read.

    Only the receiver of the message can call this endpoint.
    Calling it on an already-read message is safe (idempotent).

    Args:
        conversation_id (UUID): Conversation UUID from the URL path.
        message_id (UUID): Message UUID from the URL path.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Updated is_read status for the message.
    """
    return MessagingService.mark_message_as_read(
        db, current_user, conversation_id, message_id
    )

"""
Router for messaging endpoints (Module 9).

All endpoints require Bearer JWT authentication.
Prefix: /conversations
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

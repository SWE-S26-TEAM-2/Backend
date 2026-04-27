"""
Pydantic schemas for Messaging request/response validation.

Defines the data contracts for creating conversations
and sending messages, including optional track/playlist sharing.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator  # type: ignore


class CreateConversationRequest(BaseModel):
    """
    Schema for creating or retrieving a 1-to-1 conversation.

    Args:
        username (str): Username of the other user.
    """

    username: str


class SendMessageRequest(BaseModel):
    """
    Schema for sending a message inside a conversation.

    At least one of content, track_id, or playlist_id must be provided.
    content is capped at 2000 characters.

    Args:
        content (str, optional): The message text.
        track_id (UUID, optional): UUID of a track to share.
        playlist_id (UUID, optional): UUID of a playlist to share.
    """

    content: Optional[str] = Field(None, max_length=2000)
    track_id: Optional[UUID] = None
    playlist_id: Optional[UUID] = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        """
        Ensure the message has something to send.
        Rejects requests where all three fields are empty.
        """
        if not self.content and not self.track_id and not self.playlist_id:
            raise ValueError(
                "A message must have content, a track_id, or a playlist_id."
            )
        return self


class MarkReadRequest(BaseModel):
    """
    Schema for marking a message as read.

    No body fields needed — the message_id comes from the URL path.
    This class is kept for potential future fields (e.g. bulk read).
    """

    pass

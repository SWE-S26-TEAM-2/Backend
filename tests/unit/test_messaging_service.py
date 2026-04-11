"""
Unit tests for Module 9: Messaging & Track Sharing.

Tests MessagingService in isolation using MagicMock.
No real database needed.

Every test follows the same 3 steps:
  1. SETUP  — control what the repositories return
  2. CALL   — call the service method directly
  3. CHECK  — assert the result or the exception
"""

import uuid
from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException

from app.services.messaging_service import MessagingService  # type: ignore


# ══════════════════════════════════════════════════════
# CREATE / GET CONVERSATION TESTS
# ══════════════════════════════════════════════════════


class TestCreateOrGetConversation:
    """Tests for MessagingService.create_or_get_conversation()"""

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_create_new_conversation_success(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        No existing conversation between the two users.
        A new one must be created and its ID returned.
        Expect success=True and conversation_id in the response.
        """
        # SETUP
        participant_id = uuid.uuid4()
        participant = MagicMock()
        participant.user_id = participant_id

        mock_user_repo.get_by_id.return_value = participant
        mock_conv_repo.get_by_participants.return_value = None

        new_conv = MagicMock()
        new_conv.conversation_id = uuid.uuid4()
        mock_conv_repo.create.return_value = new_conv

        data = MagicMock()
        data.participant_id = str(participant_id)

        # CALL
        result = MessagingService.create_or_get_conversation(
            mock_db, verified_user, data
        )

        # CHECK
        assert result["success"] is True
        assert "conversation_id" in result["data"]
        mock_conv_repo.create.assert_called_once()

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_returns_existing_conversation_instead_of_creating(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        A conversation already exists between the two users.
        Must return it without creating a duplicate.
        create() must NOT be called.
        """
        # SETUP
        participant_id = uuid.uuid4()
        participant = MagicMock()

        mock_user_repo.get_by_id.return_value = participant

        existing_conv = MagicMock()
        existing_conv.conversation_id = uuid.uuid4()
        mock_conv_repo.get_by_participants.return_value = existing_conv

        data = MagicMock()
        data.participant_id = str(participant_id)

        # CALL
        result = MessagingService.create_or_get_conversation(
            mock_db, verified_user, data
        )

        # CHECK
        assert result["success"] is True
        assert str(existing_conv.conversation_id) == result["data"]["conversation_id"]
        mock_conv_repo.create.assert_not_called()

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_conversation_with_self_returns_400(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        User tries to create a conversation with themselves.
        Expect 400 Bad Request with 'yourself' in the detail.
        """
        # SETUP
        data = MagicMock()
        data.participant_id = str(verified_user.user_id)

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.create_or_get_conversation(mock_db, verified_user, data)

        assert exc_info.value.status_code == 400
        assert "yourself" in exc_info.value.detail.lower()

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_invalid_participant_uuid_returns_400(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        participant_id is not a valid UUID string.
        Expect 400 Bad Request with 'invalid' in the detail.
        """
        # SETUP
        data = MagicMock()
        data.participant_id = "this-is-not-a-uuid"

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.create_or_get_conversation(mock_db, verified_user, data)

        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_nonexistent_participant_returns_400(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        Participant UUID does not match any user in the database.
        Expect 400 Bad Request with 'does not exist' in the detail.
        """
        # SETUP
        mock_user_repo.get_by_id.return_value = None

        data = MagicMock()
        data.participant_id = str(uuid.uuid4())

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.create_or_get_conversation(mock_db, verified_user, data)

        assert exc_info.value.status_code == 400
        assert "does not exist" in exc_info.value.detail.lower()


# ══════════════════════════════════════════════════════
# GET USER CONVERSATIONS TESTS
# ══════════════════════════════════════════════════════


class TestGetUserConversations:
    """Tests for MessagingService.get_user_conversations()"""

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_returns_empty_list_when_no_conversations(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        User has no conversations at all.
        Expect success=True and an empty data list.
        """
        # SETUP
        mock_conv_repo.get_all_by_user.return_value = []

        # CALL
        result = MessagingService.get_user_conversations(mock_db, verified_user)

        # CHECK
        assert result["success"] is True
        assert result["data"] == []

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_returns_correct_number_of_conversations(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        User has one conversation. List must have exactly one entry.
        """
        # SETUP
        user1 = MagicMock()
        user1.user_id = uuid.uuid4()
        user1.display_name = "User A"
        user1.profile_picture = None

        user2 = MagicMock()
        user2.user_id = uuid.uuid4()
        user2.display_name = "User B"
        user2.profile_picture = None

        conv = MagicMock()
        conv.conversation_id = uuid.uuid4()
        conv.user1_id = user1.user_id
        conv.user2_id = user2.user_id
        conv.created_at = None

        mock_conv_repo.get_all_by_user.return_value = [conv]
        mock_user_repo.get_by_id.side_effect = [user1, user2]

        # CALL
        result = MessagingService.get_user_conversations(mock_db, verified_user)

        # CHECK
        assert len(result["data"]) == 1

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_each_conversation_has_two_participants(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        Each conversation entry must contain exactly two participants.
        """
        # SETUP
        user1 = MagicMock()
        user1.user_id = uuid.uuid4()
        user1.display_name = "User A"
        user1.profile_picture = None

        user2 = MagicMock()
        user2.user_id = uuid.uuid4()
        user2.display_name = "User B"
        user2.profile_picture = None

        conv = MagicMock()
        conv.conversation_id = uuid.uuid4()
        conv.user1_id = user1.user_id
        conv.user2_id = user2.user_id
        conv.created_at = None

        mock_conv_repo.get_all_by_user.return_value = [conv]
        mock_user_repo.get_by_id.side_effect = [user1, user2]

        # CALL
        result = MessagingService.get_user_conversations(mock_db, verified_user)

        # CHECK
        participants = result["data"][0]["participants"]
        assert len(participants) == 2

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_each_conversation_has_required_fields(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        Each conversation entry must have:
        conversation_id, created_at, and participants.
        """
        # SETUP
        user1 = MagicMock()
        user1.user_id = uuid.uuid4()
        user1.display_name = "User A"
        user1.profile_picture = None

        user2 = MagicMock()
        user2.user_id = uuid.uuid4()
        user2.display_name = "User B"
        user2.profile_picture = None

        conv = MagicMock()
        conv.conversation_id = uuid.uuid4()
        conv.user1_id = user1.user_id
        conv.user2_id = user2.user_id
        conv.created_at = None

        mock_conv_repo.get_all_by_user.return_value = [conv]
        mock_user_repo.get_by_id.side_effect = [user1, user2]

        # CALL
        result = MessagingService.get_user_conversations(mock_db, verified_user)

        # CHECK
        entry = result["data"][0]
        assert "conversation_id" in entry
        assert "created_at" in entry
        assert "participants" in entry

    @patch("app.services.messaging_service.ConversationRepository")
    @patch("app.services.messaging_service.UserRepository")
    def test_participant_info_has_required_fields(
        self, mock_user_repo, mock_conv_repo, mock_db, verified_user
    ):
        """
        Each participant in the response must have:
        user_id, display_name, and profile_picture.
        """
        # SETUP
        user1 = MagicMock()
        user1.user_id = uuid.uuid4()
        user1.display_name = "User A"
        user1.profile_picture = None

        user2 = MagicMock()
        user2.user_id = uuid.uuid4()
        user2.display_name = "User B"
        user2.profile_picture = None

        conv = MagicMock()
        conv.conversation_id = uuid.uuid4()
        conv.user1_id = user1.user_id
        conv.user2_id = user2.user_id
        conv.created_at = None

        mock_conv_repo.get_all_by_user.return_value = [conv]
        mock_user_repo.get_by_id.side_effect = [user1, user2]

        # CALL
        result = MessagingService.get_user_conversations(mock_db, verified_user)

        # CHECK
        for participant in result["data"][0]["participants"]:
            assert "user_id" in participant
            assert "display_name" in participant
            assert "profile_picture" in participant


# ══════════════════════════════════════════════════════
# DELETE CONVERSATION TESTS
# ══════════════════════════════════════════════════════


class TestDeleteConversation:
    """Tests for MessagingService.delete_conversation()"""

    @patch("app.services.messaging_service.ConversationRepository")
    def test_delete_success(self, mock_conv_repo, mock_db, verified_user):
        """
        A participant deletes their conversation.
        Expect success=True and delete called once.
        """
        # SETUP
        conv = MagicMock()
        conv.conversation_id = uuid.uuid4()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        # CALL
        result = MessagingService.delete_conversation(
            mock_db, verified_user, conv.conversation_id
        )

        # CHECK
        assert result["success"] is True
        mock_conv_repo.delete.assert_called_once_with(mock_db, conv)

    @patch("app.services.messaging_service.ConversationRepository")
    def test_delete_nonexistent_conversation_returns_404(
        self, mock_conv_repo, mock_db, verified_user
    ):
        """
        Conversation does not exist.
        Expect 404 Not Found.
        """
        # SETUP
        mock_conv_repo.get_by_id.return_value = None

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.delete_conversation(mock_db, verified_user, uuid.uuid4())

        assert exc_info.value.status_code == 404

    @patch("app.services.messaging_service.ConversationRepository")
    def test_delete_by_non_participant_returns_403(
        self, mock_conv_repo, mock_db, verified_user
    ):
        """
        User is not part of the conversation.
        Expect 403 Forbidden.
        """
        # SETUP
        conv = MagicMock()
        conv.conversation_id = uuid.uuid4()
        conv.user1_id = str(uuid.uuid4())
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.delete_conversation(
                mock_db, verified_user, conv.conversation_id
            )

        assert exc_info.value.status_code == 403

    @patch("app.services.messaging_service.ConversationRepository")
    def test_delete_does_not_call_delete_when_not_participant(
        self, mock_conv_repo, mock_db, verified_user
    ):
        """
        If user is not a participant, delete() must never be called.
        """
        # SETUP
        conv = MagicMock()
        conv.conversation_id = uuid.uuid4()
        conv.user1_id = str(uuid.uuid4())
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        # CALL + CHECK
        with pytest.raises(HTTPException):
            MessagingService.delete_conversation(
                mock_db, verified_user, conv.conversation_id
            )

        mock_conv_repo.delete.assert_not_called()


# ══════════════════════════════════════════════════════
# GET MESSAGES TESTS
# ══════════════════════════════════════════════════════


class TestGetMessages:
    """Tests for MessagingService.get_messages()"""

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_get_messages_success(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Participant retrieves messages from their conversation.
        Expect success=True and the message content in data.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        msg = MagicMock()
        msg.message_id = uuid.uuid4()
        msg.sender_id = verified_user.user_id
        msg.receiver_id = uuid.uuid4()
        msg.content = "Hello!"
        msg.track_id = None
        msg.playlist_id = None
        msg.is_read = False
        msg.created_at = None

        mock_msg_repo.get_by_conversation.return_value = [msg]

        # CALL
        result = MessagingService.get_messages(
            mock_db, verified_user, conv.conversation_id
        )

        # CHECK
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["content"] == "Hello!"

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_get_messages_empty_conversation(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Conversation exists but has no messages.
        Expect success=True with an empty data list.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv
        mock_msg_repo.get_by_conversation.return_value = []

        # CALL
        result = MessagingService.get_messages(
            mock_db, verified_user, conv.conversation_id
        )

        # CHECK
        assert result["success"] is True
        assert result["data"] == []

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_get_messages_nonexistent_conversation_returns_404(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Conversation does not exist.
        Expect 404 Not Found.
        """
        # SETUP
        mock_conv_repo.get_by_id.return_value = None

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.get_messages(mock_db, verified_user, uuid.uuid4())

        assert exc_info.value.status_code == 404

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_get_messages_non_participant_returns_403(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        User is not part of the conversation.
        Expect 403 Forbidden.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(uuid.uuid4())
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.get_messages(mock_db, verified_user, uuid.uuid4())

        assert exc_info.value.status_code == 403

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_each_message_has_required_fields(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Each message in the response must have all required fields.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        msg = MagicMock()
        msg.message_id = uuid.uuid4()
        msg.sender_id = verified_user.user_id
        msg.receiver_id = uuid.uuid4()
        msg.content = "Test"
        msg.track_id = None
        msg.playlist_id = None
        msg.is_read = False
        msg.created_at = None

        mock_msg_repo.get_by_conversation.return_value = [msg]

        # CALL
        result = MessagingService.get_messages(
            mock_db, verified_user, conv.conversation_id
        )

        # CHECK
        entry = result["data"][0]
        assert "id" in entry
        assert "sender_id" in entry
        assert "receiver_id" in entry
        assert "content" in entry
        assert "track_id" in entry
        assert "playlist_id" in entry
        assert "is_read" in entry
        assert "created_at" in entry


# ══════════════════════════════════════════════════════
# SEND MESSAGE TESTS
# ══════════════════════════════════════════════════════


class TestSendMessage:
    """Tests for MessagingService.send_message()"""

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_send_text_message_success(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Participant sends a plain text message.
        Expect success=True with correct content and is_read=False.
        """
        # SETUP
        other_id = uuid.uuid4()
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(other_id)
        mock_conv_repo.get_by_id.return_value = conv

        created_msg = MagicMock()
        created_msg.message_id = uuid.uuid4()
        created_msg.sender_id = verified_user.user_id
        created_msg.receiver_id = other_id
        created_msg.content = "Hello!"
        created_msg.track_id = None
        created_msg.playlist_id = None
        created_msg.is_read = False
        created_msg.created_at = None
        mock_msg_repo.create.return_value = created_msg

        data = MagicMock()
        data.content = "Hello!"
        data.track_id = None
        data.playlist_id = None

        # CALL
        result = MessagingService.send_message(
            mock_db, verified_user, conv.conversation_id, data
        )

        # CHECK
        assert result["success"] is True
        assert result["data"]["content"] == "Hello!"
        assert result["data"]["is_read"] is False

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_send_message_with_track_id(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        User shares a track (no text content).
        Expect success=True with track_id set and content None.
        """
        # SETUP
        other_id = uuid.uuid4()
        track_id = uuid.uuid4()

        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(other_id)
        mock_conv_repo.get_by_id.return_value = conv

        created_msg = MagicMock()
        created_msg.message_id = uuid.uuid4()
        created_msg.sender_id = verified_user.user_id
        created_msg.receiver_id = other_id
        created_msg.content = None
        created_msg.track_id = track_id
        created_msg.playlist_id = None
        created_msg.is_read = False
        created_msg.created_at = None
        mock_msg_repo.create.return_value = created_msg

        data = MagicMock()
        data.content = None
        data.track_id = track_id
        data.playlist_id = None

        # CALL
        result = MessagingService.send_message(
            mock_db, verified_user, conv.conversation_id, data
        )

        # CHECK
        assert result["success"] is True
        assert result["data"]["track_id"] == str(track_id)
        assert result["data"]["content"] is None

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_send_message_receiver_is_auto_detected(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        MessageRepository.create must be called exactly once.
        """
        # SETUP
        other_id = uuid.uuid4()
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(other_id)
        mock_conv_repo.get_by_id.return_value = conv

        created_msg = MagicMock()
        created_msg.message_id = uuid.uuid4()
        created_msg.sender_id = verified_user.user_id
        created_msg.receiver_id = other_id
        created_msg.content = "Hi"
        created_msg.track_id = None
        created_msg.playlist_id = None
        created_msg.is_read = False
        created_msg.created_at = None
        mock_msg_repo.create.return_value = created_msg

        data = MagicMock()
        data.content = "Hi"
        data.track_id = None
        data.playlist_id = None

        # CALL
        MessagingService.send_message(
            mock_db, verified_user, conv.conversation_id, data
        )

        # CHECK
        mock_msg_repo.create.assert_called_once()

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_send_message_nonexistent_conversation_returns_404(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Conversation does not exist.
        Expect 404 Not Found.
        """
        # SETUP
        mock_conv_repo.get_by_id.return_value = None

        data = MagicMock()
        data.content = "Hello!"

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.send_message(mock_db, verified_user, uuid.uuid4(), data)

        assert exc_info.value.status_code == 404

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_send_message_non_participant_returns_403(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        User is not part of the conversation.
        Expect 403 Forbidden.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(uuid.uuid4())
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        data = MagicMock()
        data.content = "Intruding!"

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.send_message(mock_db, verified_user, uuid.uuid4(), data)

        assert exc_info.value.status_code == 403

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_send_message_does_not_create_when_not_participant(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        If user is not a participant, create must never be called.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(uuid.uuid4())
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        data = MagicMock()
        data.content = "Intruding!"

        # CALL + CHECK
        with pytest.raises(HTTPException):
            MessagingService.send_message(mock_db, verified_user, uuid.uuid4(), data)

        mock_msg_repo.create.assert_not_called()


# ══════════════════════════════════════════════════════
# MARK AS READ TESTS
# ══════════════════════════════════════════════════════


class TestMarkMessageAsRead:
    """
    Tests for MessagingService.mark_message_as_read()

    The service now uses MessageRepository.get_by_id to look up
    the message, so we mock MessageRepository — not db.query.
    No @patch for Message model needed anymore.
    """

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_mark_as_read_success(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Receiver marks a message as read.
        Expect success=True and is_read=True in the response.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        msg = MagicMock()
        msg.message_id = uuid.uuid4()
        msg.receiver_id = str(verified_user.user_id)
        msg.is_read = False

        # Service calls MessageRepository.get_by_id — mock it here
        mock_msg_repo.get_by_id.return_value = msg

        updated_msg = MagicMock()
        updated_msg.message_id = msg.message_id
        updated_msg.is_read = True
        mock_msg_repo.mark_as_read.return_value = updated_msg

        # CALL
        result = MessagingService.mark_message_as_read(
            mock_db, verified_user, conv.conversation_id, msg.message_id
        )

        # CHECK
        assert result["success"] is True
        assert result["data"]["is_read"] is True
        mock_msg_repo.mark_as_read.assert_called_once_with(mock_db, msg)

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_sender_cannot_mark_own_message_as_read(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Sender tries to mark their own message as read.
        Only the receiver can do this.
        Expect 403 Forbidden.
        """
        # SETUP
        other_id = uuid.uuid4()
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(other_id)
        mock_conv_repo.get_by_id.return_value = conv

        msg = MagicMock()
        msg.message_id = uuid.uuid4()
        # receiver is the OTHER user — verified_user is the sender
        msg.receiver_id = str(other_id)
        msg.is_read = False

        mock_msg_repo.get_by_id.return_value = msg

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.mark_message_as_read(
                mock_db, verified_user, conv.conversation_id, msg.message_id
            )

        assert exc_info.value.status_code == 403

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_mark_already_read_message_is_idempotent(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Message is already marked as read.
        Must return success without calling mark_as_read again.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        msg = MagicMock()
        msg.message_id = uuid.uuid4()
        msg.receiver_id = str(verified_user.user_id)
        msg.is_read = True  # already read

        mock_msg_repo.get_by_id.return_value = msg

        # CALL
        result = MessagingService.mark_message_as_read(
            mock_db, verified_user, conv.conversation_id, msg.message_id
        )

        # CHECK
        assert result["success"] is True
        assert result["data"]["is_read"] is True
        # mark_as_read must NOT be called again
        mock_msg_repo.mark_as_read.assert_not_called()

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_message_not_found_returns_404(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Message does not exist.
        Expect 404 Not Found.
        """
        # SETUP
        conv = MagicMock()
        conv.user1_id = str(verified_user.user_id)
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        # get_by_id returns None — message not found
        mock_msg_repo.get_by_id.return_value = None

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.mark_message_as_read(
                mock_db, verified_user, conv.conversation_id, uuid.uuid4()
            )

        assert exc_info.value.status_code == 404

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_conversation_not_found_returns_404(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        Conversation does not exist.
        Expect 404 Not Found.
        """
        # SETUP
        mock_conv_repo.get_by_id.return_value = None

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.mark_message_as_read(
                mock_db, verified_user, uuid.uuid4(), uuid.uuid4()
            )

        assert exc_info.value.status_code == 404

    @patch("app.services.messaging_service.MessageRepository")
    @patch("app.services.messaging_service.ConversationRepository")
    def test_non_participant_cannot_mark_as_read(
        self, mock_conv_repo, mock_msg_repo, mock_db, verified_user
    ):
        """
        User is not part of the conversation at all.
        Expect 403 Forbidden.
        """
        # SETUP — neither user1 nor user2 matches verified_user
        conv = MagicMock()
        conv.user1_id = str(uuid.uuid4())
        conv.user2_id = str(uuid.uuid4())
        mock_conv_repo.get_by_id.return_value = conv

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            MessagingService.mark_message_as_read(
                mock_db, verified_user, conv.conversation_id, uuid.uuid4()
            )

        assert exc_info.value.status_code == 403

"""
Unit tests for Module 3: Followers & Social Graph.

Tests FollowerService and BlockService in isolation using
MagicMock — no real database needed.

Every test follows the same 3 steps:
  1. SETUP  — control what the repositories return
  2. CALL   — call the service method directly
  3. CHECK  — assert the result or the exception
"""

import uuid
from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException

from app.services.follower_service import FollowerService  # type: ignore
from app.services.block_service import BlockService  # type: ignore

# ══════════════════════════════════════════════════════
# FOLLOW TESTS
# ══════════════════════════════════════════════════════


class TestFollowUser:
    """Tests for FollowerService.follow_user()"""

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_follow_success(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        User A follows User B successfully.
        Expect success=True and a message containing target's name.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.display_name = "DJ Khaled"
        target.follower_count = 0
        verified_user.following_count = 0

        mock_user_repo.get_by_id.return_value = target
        mock_follow_repo.get_follow.return_value = None  # not following yet

        # CALL
        result = FollowerService.follow_user(mock_db, verified_user, target.user_id)

        # CHECK
        assert result["success"] is True
        assert "DJ Khaled" in result["message"]
        mock_follow_repo.create_follow.assert_called_once()

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_follow_yourself_returns_400(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        User tries to follow themselves.
        Expect 400 Bad Request with 'yourself' in the detail.
        """
        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            FollowerService.follow_user(mock_db, verified_user, verified_user.user_id)

        assert exc_info.value.status_code == 400
        assert "yourself" in exc_info.value.detail.lower()

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_follow_nonexistent_user_returns_404(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        Target user does not exist in the database.
        Expect 404 Not Found.
        """
        # SETUP — repo returns None, meaning user not found
        mock_user_repo.get_by_id.return_value = None

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            FollowerService.follow_user(mock_db, verified_user, uuid.uuid4())

        assert exc_info.value.status_code == 404

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_follow_already_following_returns_400(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        User tries to follow someone they already follow.
        Expect 400 Bad Request with 'already following' in the detail.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.display_name = "DJ Khaled"

        mock_user_repo.get_by_id.return_value = target
        # An existing follow record is found
        mock_follow_repo.get_follow.return_value = MagicMock()

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            FollowerService.follow_user(mock_db, verified_user, target.user_id)

        assert exc_info.value.status_code == 400
        assert "already following" in exc_info.value.detail.lower()

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_follow_calls_update_fields_for_both_users(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        After following, update_fields must be called for both
        the current user (following_count) and the target (follower_count).
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.display_name = "DJ Khaled"
        target.follower_count = 5
        verified_user.following_count = 3

        mock_user_repo.get_by_id.return_value = target
        mock_follow_repo.get_follow.return_value = None

        # CALL
        FollowerService.follow_user(mock_db, verified_user, target.user_id)

        # CHECK — update_fields called twice (current_user + target)
        assert mock_user_repo.update_fields.call_count == 2

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_follow_creates_follow_record_with_correct_ids(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        The follow record must be created with the correct
        follower_id (current user) and following_id (target).
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.display_name = "DJ Khaled"
        target.follower_count = 0
        verified_user.following_count = 0

        mock_user_repo.get_by_id.return_value = target
        mock_follow_repo.get_follow.return_value = None

        # CALL
        FollowerService.follow_user(mock_db, verified_user, target.user_id)

        # CHECK
        mock_follow_repo.create_follow.assert_called_once_with(
            mock_db, verified_user.user_id, target.user_id
        )


# ══════════════════════════════════════════════════════
# UNFOLLOW TESTS
# ══════════════════════════════════════════════════════


class TestUnfollowUser:
    """Tests for FollowerService.unfollow_user()"""

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_unfollow_success(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        User unfollows someone they follow.
        Expect success=True.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.follower_count = 1
        verified_user.following_count = 1

        existing_follow = MagicMock()
        mock_follow_repo.get_follow.return_value = existing_follow
        mock_user_repo.get_by_id.return_value = target

        # CALL
        result = FollowerService.unfollow_user(mock_db, verified_user, target.user_id)

        # CHECK
        assert result["success"] is True

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_unfollow_not_following_returns_404(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        User tries to unfollow someone they never followed.
        Expect 404 Not Found with 'not following' in the detail.
        """
        # SETUP — no follow record found
        mock_follow_repo.get_follow.return_value = None

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            FollowerService.unfollow_user(mock_db, verified_user, uuid.uuid4())

        assert exc_info.value.status_code == 404
        assert "not following" in exc_info.value.detail.lower()

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_unfollow_deletes_follow_record(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        Unfollow must call delete_follow with the correct follow record.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.follower_count = 1
        verified_user.following_count = 1

        follow_record = MagicMock()
        mock_follow_repo.get_follow.return_value = follow_record
        mock_user_repo.get_by_id.return_value = target

        # CALL
        FollowerService.unfollow_user(mock_db, verified_user, target.user_id)

        # CHECK
        mock_follow_repo.delete_follow.assert_called_once_with(mock_db, follow_record)

    @patch("app.services.follower_service.FollowRepository")
    @patch("app.services.follower_service.UserRepository")
    def test_unfollow_calls_update_fields_for_both_users(
        self, mock_user_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        Unfollow must call update_fields for both users
        to decrement their counters.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.follower_count = 2
        verified_user.following_count = 2

        mock_follow_repo.get_follow.return_value = MagicMock()
        mock_user_repo.get_by_id.return_value = target

        # CALL
        FollowerService.unfollow_user(mock_db, verified_user, target.user_id)

        # CHECK
        assert mock_user_repo.update_fields.call_count == 2


# ══════════════════════════════════════════════════════
# BLOCK TESTS
# ══════════════════════════════════════════════════════


class TestBlockUser:
    """Tests for BlockService.block_user()"""

    @patch("app.services.block_service.FollowRepository")
    @patch("app.services.block_service.BlockRepository")
    @patch("app.services.block_service.UserRepository")
    def test_block_success(
        self, mock_user_repo, mock_block_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        User blocks another user successfully.
        Expect success=True and message containing 'blocked'.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()

        mock_user_repo.get_by_id.return_value = target
        mock_block_repo.get_block.return_value = None
        mock_follow_repo.get_follow.return_value = None

        # CALL
        result = BlockService.block_user(mock_db, verified_user, target.user_id)

        # CHECK
        assert result["success"] is True
        assert "blocked" in result["message"].lower()
        mock_block_repo.create_block.assert_called_once()

    @patch("app.services.block_service.FollowRepository")
    @patch("app.services.block_service.BlockRepository")
    @patch("app.services.block_service.UserRepository")
    def test_block_yourself_returns_400(
        self, mock_user_repo, mock_block_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        User tries to block themselves.
        Expect 400 Bad Request with 'yourself' in the detail.
        """
        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            BlockService.block_user(mock_db, verified_user, verified_user.user_id)

        assert exc_info.value.status_code == 400
        assert "yourself" in exc_info.value.detail.lower()

    @patch("app.services.block_service.FollowRepository")
    @patch("app.services.block_service.BlockRepository")
    @patch("app.services.block_service.UserRepository")
    def test_block_nonexistent_user_returns_404(
        self, mock_user_repo, mock_block_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        Target user does not exist in the database.
        Expect 404 Not Found.
        """
        # SETUP
        mock_user_repo.get_by_id.return_value = None

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            BlockService.block_user(mock_db, verified_user, uuid.uuid4())

        assert exc_info.value.status_code == 404

    @patch("app.services.block_service.FollowRepository")
    @patch("app.services.block_service.BlockRepository")
    @patch("app.services.block_service.UserRepository")
    def test_block_already_blocked_returns_400(
        self, mock_user_repo, mock_block_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        User tries to block someone they already blocked.
        Expect 400 Bad Request with 'already blocked' in the detail.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()

        mock_user_repo.get_by_id.return_value = target
        mock_block_repo.get_block.return_value = MagicMock()

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            BlockService.block_user(mock_db, verified_user, target.user_id)

        assert exc_info.value.status_code == 400
        assert "already blocked" in exc_info.value.detail.lower()

    @patch("app.services.block_service.FollowRepository")
    @patch("app.services.block_service.BlockRepository")
    @patch("app.services.block_service.UserRepository")
    def test_block_auto_removes_follow_current_to_target(
        self, mock_user_repo, mock_block_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        When blocking, any existing follow from current→target
        must be automatically deleted.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.follower_count = 1
        verified_user.following_count = 1

        mock_user_repo.get_by_id.return_value = target
        mock_block_repo.get_block.return_value = None

        existing_follow = MagicMock()
        mock_follow_repo.get_follow.side_effect = [
            existing_follow,  # first call: current→target (exists)
            None,  # second call: target→current (doesn't exist)
        ]

        # CALL
        BlockService.block_user(mock_db, verified_user, target.user_id)

        # CHECK — the follow was deleted
        mock_follow_repo.delete_follow.assert_called_with(mock_db, existing_follow)

    @patch("app.services.block_service.FollowRepository")
    @patch("app.services.block_service.BlockRepository")
    @patch("app.services.block_service.UserRepository")
    def test_block_auto_removes_reverse_follow(
        self, mock_user_repo, mock_block_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        When blocking, any existing follow from target→current
        must also be automatically deleted.
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()
        target.following_count = 1
        verified_user.follower_count = 1

        mock_user_repo.get_by_id.return_value = target
        mock_block_repo.get_block.return_value = None

        reverse_follow = MagicMock()
        mock_follow_repo.get_follow.side_effect = [
            None,  # first call: current→target (doesn't exist)
            reverse_follow,  # second call: target→current (exists)
        ]

        # CALL
        BlockService.block_user(mock_db, verified_user, target.user_id)

        # CHECK — the reverse follow was deleted
        mock_follow_repo.delete_follow.assert_called_with(mock_db, reverse_follow)

    @patch("app.services.block_service.FollowRepository")
    @patch("app.services.block_service.BlockRepository")
    @patch("app.services.block_service.UserRepository")
    def test_block_creates_block_record_with_correct_ids(
        self, mock_user_repo, mock_block_repo, mock_follow_repo, mock_db, verified_user
    ):
        """
        The block record must be created with the correct
        blocker_id (current user) and blocked_id (target).
        """
        # SETUP
        target = MagicMock()
        target.user_id = uuid.uuid4()

        mock_user_repo.get_by_id.return_value = target
        mock_block_repo.get_block.return_value = None
        mock_follow_repo.get_follow.return_value = None

        # CALL
        BlockService.block_user(mock_db, verified_user, target.user_id)

        # CHECK
        mock_block_repo.create_block.assert_called_once_with(
            mock_db, verified_user.user_id, target.user_id
        )


# ══════════════════════════════════════════════════════
# UNBLOCK TESTS
# ══════════════════════════════════════════════════════


class TestUnblockUser:
    """Tests for BlockService.unblock_user()"""

    @patch("app.services.block_service.BlockRepository")
    def test_unblock_success(self, mock_block_repo, mock_db, verified_user):
        """
        User unblocks someone they previously blocked.
        Expect success=True and message containing 'unblocked'.
        """
        # SETUP
        target_id = uuid.uuid4()
        existing_block = MagicMock()
        mock_block_repo.get_block.return_value = existing_block

        # CALL
        result = BlockService.unblock_user(mock_db, verified_user, target_id)

        # CHECK
        assert result["success"] is True
        assert "unblocked" in result["message"].lower()

    @patch("app.services.block_service.BlockRepository")
    def test_unblock_not_blocked_returns_404(
        self, mock_block_repo, mock_db, verified_user
    ):
        """
        User tries to unblock someone they never blocked.
        Expect 404 Not Found with 'not blocked' in the detail.
        """
        # SETUP — no block record found
        mock_block_repo.get_block.return_value = None

        # CALL + CHECK
        with pytest.raises(HTTPException) as exc_info:
            BlockService.unblock_user(mock_db, verified_user, uuid.uuid4())

        assert exc_info.value.status_code == 404
        assert "not blocked" in exc_info.value.detail.lower()

    @patch("app.services.block_service.BlockRepository")
    def test_unblock_deletes_block_record(
        self, mock_block_repo, mock_db, verified_user
    ):
        """
        Unblock must call delete_block with the correct block record.
        """
        # SETUP
        target_id = uuid.uuid4()
        block_record = MagicMock()
        mock_block_repo.get_block.return_value = block_record

        # CALL
        BlockService.unblock_user(mock_db, verified_user, target_id)

        # CHECK
        mock_block_repo.delete_block.assert_called_once_with(mock_db, block_record)

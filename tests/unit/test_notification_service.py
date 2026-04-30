import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.notification_service import NotificationService
from tests.unit.conftest import make_fake_user

NOTIF_REPO = "app.services.notification_service.NotificationRepository"


def _make_notification(user_id=None, is_read=False):
    n = MagicMock()
    n.notification_id = uuid.uuid4()
    n.user_id = user_id or uuid.uuid4()
    n.actor_id = uuid.uuid4()
    n.notification_type = "like"
    n.target_id = uuid.uuid4()
    n.message = "Someone liked your track."
    n.is_read = is_read
    n.created_at = "2026-04-12T00:00:00Z"
    return n


def _make_notif_row(user_id=None, is_read=False):
    """Returns a (Notification, username, display_name, profile_picture) tuple as the repo now yields."""
    n = _make_notification(user_id=user_id, is_read=is_read)
    return (n, "actor_user", "Actor User", None)


class TestGetNotifications:

    @patch(NOTIF_REPO)
    def test_get_notifications_success(self, mock_repo):
        db = MagicMock()
        user = make_fake_user()
        rows = [
            _make_notif_row(user.user_id),
            _make_notif_row(user.user_id, is_read=True),
        ]
        mock_repo.get_by_user.return_value = rows

        result = NotificationService.get_notifications(db, user)

        assert result["success"] is True
        assert len(result["data"]["notifications"]) == 2
        notif = result["data"]["notifications"][0]
        assert notif["actor_username"] == "actor_user"
        assert notif["actor_display_name"] == "Actor User"
        assert notif["actor_profile_picture"] is None
        mock_repo.get_by_user.assert_called_once_with(
            db, user.user_id, limit=50, offset=0
        )

    @patch(NOTIF_REPO)
    def test_get_notifications_empty(self, mock_repo):
        db = MagicMock()
        user = make_fake_user()
        mock_repo.get_by_user.return_value = []

        result = NotificationService.get_notifications(db, user)

        assert result["success"] is True
        assert result["data"]["notifications"] == []

    @patch(NOTIF_REPO)
    def test_get_notifications_pagination(self, mock_repo):
        db = MagicMock()
        user = make_fake_user()
        mock_repo.get_by_user.return_value = []

        NotificationService.get_notifications(db, user, limit=10, offset=20)

        mock_repo.get_by_user.assert_called_once_with(
            db, user.user_id, limit=10, offset=20
        )


class TestMarkAsRead:

    @patch(NOTIF_REPO)
    def test_mark_as_read_success(self, mock_repo):
        db = MagicMock()
        user = make_fake_user()
        notif = _make_notification(user_id=user.user_id, is_read=False)
        mock_repo.get_by_id.return_value = notif

        updated = _make_notification(user_id=user.user_id, is_read=True)
        updated.notification_id = notif.notification_id
        mock_repo.mark_as_read.return_value = updated

        result = NotificationService.mark_as_read(db, user, notif.notification_id)

        assert result["success"] is True
        assert result["data"]["is_read"] is True
        mock_repo.mark_as_read.assert_called_once_with(db, notif)

    @patch(NOTIF_REPO)
    def test_mark_as_read_not_found(self, mock_repo):
        db = MagicMock()
        user = make_fake_user()
        mock_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            NotificationService.mark_as_read(db, user, uuid.uuid4())
        assert exc.value.status_code == 404

    @patch(NOTIF_REPO)
    def test_mark_as_read_not_owner(self, mock_repo):
        db = MagicMock()
        user = make_fake_user()
        # Notification belongs to a different user
        notif = _make_notification(user_id=uuid.uuid4())
        mock_repo.get_by_id.return_value = notif

        with pytest.raises(HTTPException) as exc:
            NotificationService.mark_as_read(db, user, notif.notification_id)
        assert exc.value.status_code == 403

    @patch(NOTIF_REPO)
    def test_mark_as_read_already_read_idempotent(self, mock_repo):
        db = MagicMock()
        user = make_fake_user()
        notif = _make_notification(user_id=user.user_id, is_read=True)
        mock_repo.get_by_id.return_value = notif

        result = NotificationService.mark_as_read(db, user, notif.notification_id)

        assert result["success"] is True
        assert result["data"]["is_read"] is True
        mock_repo.mark_as_read.assert_not_called()

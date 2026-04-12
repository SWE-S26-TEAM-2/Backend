import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.engagement_service import EngagementService
from tests.unit.conftest import make_fake_user


# ── Helpers ───────────────────────────────────────────────

def _make_track(owner_id=None):
    track = MagicMock()
    track.track_id = uuid.uuid4()
    track.user_id = owner_id or uuid.uuid4()
    track.title = "Test Track"
    return track


def _make_like(user_id, track_id):
    like = MagicMock()
    like.like_id = uuid.uuid4()
    like.user_id = user_id
    like.track_id = track_id
    return like


def _make_repost(user_id, track_id):
    repost = MagicMock()
    repost.repost_id = uuid.uuid4()
    repost.user_id = user_id
    repost.track_id = track_id
    return repost


def _make_comment(**overrides):
    defaults = {
        "comment_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "track_id": uuid.uuid4(),
        "content": "Nice beat!",
        "timestamp_in_track": 42,
        "parent_comment_id": None,
        "created_at": "2026-04-12T00:00:00Z",
    }
    defaults.update(overrides)
    comment = MagicMock()
    for k, v in defaults.items():
        setattr(comment, k, v)
    return comment


# ── Like Tests ────────────────────────────────────────────

TRACK_REPO = "app.services.engagement_service.TrackRepository"
LIKE_REPO = "app.services.engagement_service.LikeRepository"
REPOST_REPO = "app.services.engagement_service.RepostRepository"
COMMENT_REPO = "app.services.engagement_service.CommentRepository"
NOTIF_REPO = "app.services.engagement_service.NotificationRepository"


class TestLikeTrack:

    @patch(NOTIF_REPO)
    @patch(LIKE_REPO)
    @patch(TRACK_REPO)
    def test_like_track_success(self, mock_track, mock_like, mock_notif):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        mock_like.get_like.return_value = None
        created = _make_like(user.user_id, track.track_id)
        mock_like.create.return_value = created

        result = EngagementService.like_track(db, user, track.track_id)

        assert result["success"] is True
        assert result["message"] == "Track liked."
        mock_like.create.assert_called_once()
        mock_notif.create.assert_called_once()

    @patch(NOTIF_REPO)
    @patch(LIKE_REPO)
    @patch(TRACK_REPO)
    def test_like_own_track_no_notification(
        self, mock_track, mock_like, mock_notif
    ):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track(owner_id=user.user_id)
        mock_track.get_by_id.return_value = track
        mock_like.get_like.return_value = None
        mock_like.create.return_value = _make_like(
            user.user_id, track.track_id
        )

        result = EngagementService.like_track(db, user, track.track_id)

        assert result["success"] is True
        mock_notif.create.assert_not_called()

    @patch(LIKE_REPO)
    @patch(TRACK_REPO)
    def test_like_track_not_found(self, mock_track, mock_like):
        db = MagicMock()
        user = make_fake_user()
        mock_track.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            EngagementService.like_track(db, user, uuid.uuid4())
        assert exc.value.status_code == 404

    @patch(LIKE_REPO)
    @patch(TRACK_REPO)
    def test_like_track_already_liked(self, mock_track, mock_like):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        mock_like.get_like.return_value = _make_like(
            user.user_id, track.track_id
        )

        with pytest.raises(HTTPException) as exc:
            EngagementService.like_track(db, user, track.track_id)
        assert exc.value.status_code == 400


class TestUnlikeTrack:

    @patch(LIKE_REPO)
    @patch(TRACK_REPO)
    def test_unlike_track_success(self, mock_track, mock_like):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        existing = _make_like(user.user_id, track.track_id)
        mock_track.get_by_id.return_value = track
        mock_like.get_like.return_value = existing

        result = EngagementService.unlike_track(db, user, track.track_id)

        assert result["success"] is True
        assert result["message"] == "Track unliked."
        mock_like.delete.assert_called_once_with(db, existing)

    @patch(LIKE_REPO)
    @patch(TRACK_REPO)
    def test_unlike_track_not_found(self, mock_track, mock_like):
        db = MagicMock()
        user = make_fake_user()
        mock_track.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            EngagementService.unlike_track(db, user, uuid.uuid4())
        assert exc.value.status_code == 404

    @patch(LIKE_REPO)
    @patch(TRACK_REPO)
    def test_unlike_track_not_liked(self, mock_track, mock_like):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        mock_like.get_like.return_value = None

        with pytest.raises(HTTPException) as exc:
            EngagementService.unlike_track(db, user, track.track_id)
        assert exc.value.status_code == 400


# ── Repost Tests ──────────────────────────────────────────

class TestRepostTrack:

    @patch(NOTIF_REPO)
    @patch(REPOST_REPO)
    @patch(TRACK_REPO)
    def test_repost_track_success(self, mock_track, mock_repost, mock_notif):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        mock_repost.get_repost.return_value = None
        created = _make_repost(user.user_id, track.track_id)
        mock_repost.create.return_value = created

        result = EngagementService.repost_track(db, user, track.track_id)

        assert result["success"] is True
        assert result["message"] == "Track reposted."
        mock_repost.create.assert_called_once()
        mock_notif.create.assert_called_once()

    @patch(NOTIF_REPO)
    @patch(REPOST_REPO)
    @patch(TRACK_REPO)
    def test_repost_own_track_no_notification(
        self, mock_track, mock_repost, mock_notif
    ):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track(owner_id=user.user_id)
        mock_track.get_by_id.return_value = track
        mock_repost.get_repost.return_value = None
        mock_repost.create.return_value = _make_repost(
            user.user_id, track.track_id
        )

        result = EngagementService.repost_track(db, user, track.track_id)

        assert result["success"] is True
        mock_notif.create.assert_not_called()

    @patch(REPOST_REPO)
    @patch(TRACK_REPO)
    def test_repost_track_not_found(self, mock_track, mock_repost):
        db = MagicMock()
        user = make_fake_user()
        mock_track.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            EngagementService.repost_track(db, user, uuid.uuid4())
        assert exc.value.status_code == 404

    @patch(REPOST_REPO)
    @patch(TRACK_REPO)
    def test_repost_track_already_reposted(self, mock_track, mock_repost):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        mock_repost.get_repost.return_value = _make_repost(
            user.user_id, track.track_id
        )

        with pytest.raises(HTTPException) as exc:
            EngagementService.repost_track(db, user, track.track_id)
        assert exc.value.status_code == 400


class TestRemoveRepost:

    @patch(REPOST_REPO)
    @patch(TRACK_REPO)
    def test_remove_repost_success(self, mock_track, mock_repost):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        existing = _make_repost(user.user_id, track.track_id)
        mock_track.get_by_id.return_value = track
        mock_repost.get_repost.return_value = existing

        result = EngagementService.remove_repost(db, user, track.track_id)

        assert result["success"] is True
        assert result["message"] == "Repost removed."
        mock_repost.delete.assert_called_once_with(db, existing)

    @patch(REPOST_REPO)
    @patch(TRACK_REPO)
    def test_remove_repost_track_not_found(self, mock_track, mock_repost):
        db = MagicMock()
        user = make_fake_user()
        mock_track.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            EngagementService.remove_repost(db, user, uuid.uuid4())
        assert exc.value.status_code == 404

    @patch(REPOST_REPO)
    @patch(TRACK_REPO)
    def test_remove_repost_not_reposted(self, mock_track, mock_repost):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        mock_repost.get_repost.return_value = None

        with pytest.raises(HTTPException) as exc:
            EngagementService.remove_repost(db, user, track.track_id)
        assert exc.value.status_code == 400


# ── Comment Tests ─────────────────────────────────────────

class TestGetTrackComments:

    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_get_comments_success(self, mock_track, mock_comment):
        db = MagicMock()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        comments = [_make_comment(), _make_comment()]
        mock_comment.get_by_track.return_value = comments

        result = EngagementService.get_track_comments(db, track.track_id)

        assert result["success"] is True
        assert len(result["data"]["comments"]) == 2

    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_get_comments_track_not_found(self, mock_track, mock_comment):
        db = MagicMock()
        mock_track.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            EngagementService.get_track_comments(db, uuid.uuid4())
        assert exc.value.status_code == 404

    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_get_comments_empty(self, mock_track, mock_comment):
        db = MagicMock()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        mock_comment.get_by_track.return_value = []

        result = EngagementService.get_track_comments(db, track.track_id)

        assert result["success"] is True
        assert result["data"]["comments"] == []


class TestAddComment:

    @patch(NOTIF_REPO)
    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_add_comment_success(self, mock_track, mock_comment, mock_notif):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track

        created = _make_comment(
            user_id=user.user_id, track_id=track.track_id
        )
        mock_comment.create.return_value = created

        data = MagicMock()
        data.content = "Great track!"
        data.timestamp_in_track = 30
        data.parent_comment_id = None

        result = EngagementService.add_comment(
            db, user, track.track_id, data
        )

        assert result["success"] is True
        assert result["message"] == "Comment added."
        mock_comment.create.assert_called_once()
        mock_notif.create.assert_called_once()

    @patch(NOTIF_REPO)
    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_add_comment_own_track_no_notification(
        self, mock_track, mock_comment, mock_notif
    ):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track(owner_id=user.user_id)
        mock_track.get_by_id.return_value = track

        created = _make_comment(
            user_id=user.user_id, track_id=track.track_id
        )
        mock_comment.create.return_value = created

        data = MagicMock()
        data.content = "My own comment"
        data.timestamp_in_track = None
        data.parent_comment_id = None

        result = EngagementService.add_comment(
            db, user, track.track_id, data
        )

        assert result["success"] is True
        mock_notif.create.assert_not_called()

    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_add_comment_track_not_found(self, mock_track, mock_comment):
        db = MagicMock()
        user = make_fake_user()
        mock_track.get_by_id.return_value = None

        data = MagicMock()
        data.content = "Hello"
        data.timestamp_in_track = None
        data.parent_comment_id = None

        with pytest.raises(HTTPException) as exc:
            EngagementService.add_comment(db, user, uuid.uuid4(), data)
        assert exc.value.status_code == 404

    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_add_comment_parent_not_found(self, mock_track, mock_comment):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track
        mock_comment.get_by_id.return_value = None

        data = MagicMock()
        data.content = "Reply"
        data.timestamp_in_track = None
        data.parent_comment_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc:
            EngagementService.add_comment(
                db, user, track.track_id, data
            )
        assert exc.value.status_code == 400
        assert "Parent comment not found" in exc.value.detail

    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_add_comment_nested_reply_blocked(
        self, mock_track, mock_comment
    ):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track

        parent = _make_comment(parent_comment_id=uuid.uuid4())
        mock_comment.get_by_id.return_value = parent

        data = MagicMock()
        data.content = "Nested reply"
        data.timestamp_in_track = None
        data.parent_comment_id = parent.comment_id

        with pytest.raises(HTTPException) as exc:
            EngagementService.add_comment(
                db, user, track.track_id, data
            )
        assert exc.value.status_code == 400
        assert "max 1 level" in exc.value.detail

    @patch(NOTIF_REPO)
    @patch(COMMENT_REPO)
    @patch(TRACK_REPO)
    def test_add_reply_to_comment_success(
        self, mock_track, mock_comment, mock_notif
    ):
        db = MagicMock()
        user = make_fake_user()
        track = _make_track()
        mock_track.get_by_id.return_value = track

        parent = _make_comment(parent_comment_id=None)
        mock_comment.get_by_id.return_value = parent

        reply = _make_comment(parent_comment_id=parent.comment_id)
        mock_comment.create.return_value = reply

        data = MagicMock()
        data.content = "Nice reply"
        data.timestamp_in_track = None
        data.parent_comment_id = parent.comment_id

        result = EngagementService.add_comment(
            db, user, track.track_id, data
        )

        assert result["success"] is True
        assert result["message"] == "Comment added."

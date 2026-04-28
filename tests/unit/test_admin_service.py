from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.admin_service import AdminService
from tests.unit.conftest import make_fake_user


class FakeReport:
    def __init__(
        self,
        *,
        report_id=None,
        reporter_id=None,
        entity_type="track",
        entity_id=None,
        reason="Spam upload",
        status="open",
        reviewed_by=None,
        reviewed_at=None,
        resolution_note=None,
        created_at=None,
    ):
        self.report_id = report_id or uuid4()
        self.reporter_id = reporter_id or uuid4()
        self.entity_type = entity_type
        self.entity_id = entity_id or uuid4()
        self.reason = reason
        self.status = status
        self.reviewed_by = reviewed_by
        self.reviewed_at = reviewed_at
        self.resolution_note = resolution_note
        self.created_at = created_at or datetime.now(timezone.utc)


def test_submit_report_success(monkeypatch, mock_db, verified_user):
    track_id = uuid4()
    created_reports = []

    from app.repositories.report_repo import ReportRepository
    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db, tid: object())
    monkeypatch.setattr(
        ReportRepository,
        "get_active_by_reporter_and_entity",
        lambda db, reporter_id, entity_type, entity_id: None,
    )

    def fake_create(db, report):
        created_reports.append(report)
        return report

    monkeypatch.setattr(ReportRepository, "create", fake_create)

    data = type(
        "ReportRequest",
        (),
        {
            "entity_type": "track",
            "entity_id": track_id,
            "reason": "Spam upload",
        },
    )()

    result = AdminService.submit_report(mock_db, verified_user, data)

    assert result["success"] is True
    assert result["data"]["entity_type"] == "track"
    assert result["data"]["entity_id"] == str(track_id)
    assert len(created_reports) == 1
    assert created_reports[0].reporter_id == verified_user.user_id


def test_submit_report_rejects_duplicate_active_report(
    monkeypatch,
    mock_db,
    verified_user,
):
    from app.repositories.report_repo import ReportRepository
    from app.repositories.track_repo import TrackRepository

    monkeypatch.setattr(TrackRepository, "get_by_id", lambda db, tid: object())
    monkeypatch.setattr(
        ReportRepository,
        "get_active_by_reporter_and_entity",
        lambda db, reporter_id, entity_type, entity_id: FakeReport(),
    )

    data = type(
        "ReportRequest",
        (),
        {
            "entity_type": "track",
            "entity_id": uuid4(),
            "reason": "Spam upload",
        },
    )()

    with pytest.raises(HTTPException) as exc:
        AdminService.submit_report(mock_db, verified_user, data)

    assert exc.value.status_code == 409
    assert exc.value.detail == "You already have an active report for this entity."


def test_get_analytics_success(monkeypatch, mock_db):
    from app.models.comment import Comment
    from app.models.track import Track
    from app.models.user import User

    monkeypatch.setattr(
        AdminService,
        "_count_rows",
        lambda db, model: {
            User: 12,
            Track: 7,
            Comment: 18,
        }[model],
    )
    monkeypatch.setattr(
        AdminService,
        "_count_reports",
        lambda db, status=None: {
            None: 5,
            "open": 2,
            "under_review": 1,
            "resolved": 1,
            "dismissed": 1,
        }[status],
    )
    monkeypatch.setattr(
        AdminService,
        "_count_listening_history_since",
        lambda db, started_at: 9,
    )

    suspended_query = mock_db.query.return_value
    suspended_query.filter.return_value.count.return_value = 3

    result = AdminService.get_analytics(mock_db)

    assert result["success"] is True
    assert result["data"]["total_users"] == 12
    assert result["data"]["open_reports"] == 2
    assert result["data"]["active_streams_today"] == 9


def test_list_reports_success(monkeypatch, mock_db):
    from app.repositories.comment_repo import CommentRepository
    from app.repositories.report_repo import ReportRepository
    from app.repositories.track_repo import TrackRepository
    from app.repositories.user_repo import UserRepository

    reporter_id = uuid4()
    reviewer_id = uuid4()
    entity_id = uuid4()
    report = FakeReport(
        reporter_id=reporter_id,
        reviewed_by=reviewer_id,
        entity_type="track",
        entity_id=entity_id,
        status="under_review",
    )
    reporter = type(
        "UserObj",
        (),
        {
            "user_id": reporter_id,
            "username": "reporter",
            "display_name": "Reporter",
            "account_type": "listener",
            "is_suspended": False,
        },
    )()
    reviewer = type(
        "UserObj",
        (),
        {
            "user_id": reviewer_id,
            "username": "admin1",
            "display_name": "Admin One",
            "account_type": "listener",
            "is_suspended": False,
        },
    )()
    track = type(
        "TrackObj",
        (),
        {
            "track_id": entity_id,
            "title": "Reported Track",
            "user_id": uuid4(),
            "visibility": "public",
            "play_count": 10,
        },
    )()

    monkeypatch.setattr(
        ReportRepository,
        "list_reports",
        lambda db, status=None, entity_type=None, limit=20, offset=0: ([report], 1),
    )
    monkeypatch.setattr(
        UserRepository,
        "get_by_ids",
        lambda db, ids: [reporter, reviewer],
    )
    monkeypatch.setattr(TrackRepository, "get_by_ids", lambda db, ids: [track])
    monkeypatch.setattr(CommentRepository, "get_by_ids", lambda db, ids: [])

    result = AdminService.list_reports(mock_db, report_status="under_review")

    assert result["success"] is True
    assert result["data"]["total"] == 1
    assert result["data"]["reports"][0]["reporter"]["username"] == "reporter"
    assert result["data"]["reports"][0]["entity_preview"]["title"] == "Reported Track"


def test_review_report_not_found(monkeypatch, mock_db, verified_user):
    from app.repositories.report_repo import ReportRepository

    monkeypatch.setattr(ReportRepository, "get_by_id", lambda db, report_id: None)

    data = type(
        "ReviewRequest",
        (),
        {"status": "resolved", "resolution_note": "Handled"},
    )()

    with pytest.raises(HTTPException) as exc:
        AdminService.review_report(mock_db, uuid4(), verified_user, data)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Report not found."


def test_update_user_suspension_success(monkeypatch, mock_db, verified_user):
    from app.repositories.refresh_token_repo import RefreshTokenRepository
    from app.repositories.user_repo import UserRepository

    target_user = type(
        "UserObj",
        (),
        {
            "user_id": uuid4(),
            "username": "target",
            "display_name": "Target User",
            "is_suspended": False,
        },
    )()
    revoked = []

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db, user_id: target_user)

    def fake_update_fields(db, user, fields):
        for key, value in fields.items():
            setattr(user, key, value)
        return user

    monkeypatch.setattr(UserRepository, "update_fields", fake_update_fields)
    monkeypatch.setattr(
        RefreshTokenRepository,
        "revoke_all_for_user",
        lambda db, user_id: revoked.append(user_id),
    )

    data = type(
        "SuspensionRequest",
        (),
        {"is_suspended": True, "reason": "Repeated abuse"},
    )()

    result = AdminService.update_user_suspension(
        mock_db,
        target_user.user_id,
        verified_user,
        data,
    )

    assert result["success"] is True
    assert result["data"]["is_suspended"] is True
    assert revoked == [str(target_user.user_id)]


def test_update_user_suspension_rejects_self_suspend(
    monkeypatch,
    mock_db,
    verified_user,
):
    from app.repositories.user_repo import UserRepository

    monkeypatch.setattr(
        UserRepository,
        "get_by_id",
        lambda db, user_id: verified_user,
    )

    data = type(
        "SuspensionRequest",
        (),
        {"is_suspended": True, "reason": "Nope"},
    )()

    with pytest.raises(HTTPException) as exc:
        AdminService.update_user_suspension(
            mock_db,
            verified_user.user_id,
            verified_user,
            data,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Admins cannot suspend themselves."


def test_delete_comment_success(monkeypatch, mock_db):
    from app.repositories.comment_repo import CommentRepository

    comment = type("CommentObj", (), {"comment_id": uuid4()})()
    deleted = []

    monkeypatch.setattr(CommentRepository, "get_by_id", lambda db, cid: comment)
    monkeypatch.setattr(
        CommentRepository,
        "delete",
        lambda db, comment_obj: deleted.append(comment_obj.comment_id),
    )

    result = AdminService.delete_comment(mock_db, comment.comment_id)

    assert result["success"] is True
    assert result["message"] == "Comment deleted successfully."
    assert deleted == [comment.comment_id]


def test_delete_track_success(monkeypatch, mock_db):
    track = type(
        "TrackObj",
        (),
        {"track_id": uuid4(), "title": "Removed Track"},
    )()

    from app.services.track_service import TrackService

    monkeypatch.setattr(TrackService, "admin_delete_track", lambda db, track_id: track)

    result = AdminService.delete_track(mock_db, track.track_id)

    assert result["success"] is True
    assert result["data"]["track_id"] == str(track.track_id)
    assert result["data"]["title"] == "Removed Track"


def test_update_user_role_success(monkeypatch, mock_db, verified_user):
    from app.repositories.user_repo import UserRepository

    target_user = type(
        "UserObj",
        (),
        {
            "user_id": uuid4(),
            "username": "futureadmin",
            "display_name": "Future Admin",
            "role": "user",
        },
    )()

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db, user_id: target_user)
    monkeypatch.setattr(UserRepository, "count_by_role", lambda db, role: 2)

    def fake_update_fields(db, user, fields):
        for key, value in fields.items():
            setattr(user, key, value)
        return user

    monkeypatch.setattr(UserRepository, "update_fields", fake_update_fields)

    data = type("RoleRequest", (), {"role": "admin"})()

    result = AdminService.update_user_role(
        mock_db,
        target_user.user_id,
        verified_user,
        data,
    )

    assert result["success"] is True
    assert result["data"]["role"] == "admin"


def test_update_user_role_rejects_self_demote(monkeypatch, mock_db, verified_user):
    from app.repositories.user_repo import UserRepository

    admin_user = make_fake_user(role="admin")

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db, user_id: admin_user)

    data = type("RoleRequest", (), {"role": "user"})()

    with pytest.raises(HTTPException) as exc:
        AdminService.update_user_role(
            mock_db,
            admin_user.user_id,
            admin_user,
            data,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Admins cannot remove their own admin role."


def test_update_user_role_rejects_last_admin_demote(
    monkeypatch, mock_db, verified_user
):
    from app.repositories.user_repo import UserRepository

    target_admin = make_fake_user(role="admin")

    monkeypatch.setattr(UserRepository, "get_by_id", lambda db, user_id: target_admin)
    monkeypatch.setattr(UserRepository, "count_by_role", lambda db, role: 1)

    data = type("RoleRequest", (), {"role": "user"})()

    with pytest.raises(HTTPException) as exc:
        AdminService.update_user_role(
            mock_db,
            target_admin.user_id,
            verified_user,
            data,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Cannot remove the last admin."

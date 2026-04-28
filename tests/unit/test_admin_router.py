from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_admin, get_current_user
from app.database.database import get_db
from app.main import app
from app.services.admin_service import AdminService

client = TestClient(app)


class FakeUser:
    def __init__(self, user_id=None, role="user"):
        self.user_id = user_id or uuid4()
        self.role = role


class DummyDB:
    pass


def override_get_db():
    yield DummyDB()


def setup_module(module):
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(module):
    app.dependency_overrides.clear()


def test_submit_report_success(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: FakeUser()

    report_id = uuid4()
    entity_id = uuid4()

    monkeypatch.setattr(
        AdminService,
        "submit_report",
        lambda db, current_user, data: {
            "success": True,
            "message": "Report submitted successfully.",
            "data": {
                "report_id": str(report_id),
                "entity_type": data.entity_type,
                "entity_id": str(entity_id),
                "status": "open",
                "created_at": "2026-04-28T19:00:00+00:00",
            },
        },
    )

    response = client.post(
        "/reports",
        json={
            "entity_type": "track",
            "entity_id": str(entity_id),
            "reason": "Spam upload",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["report_id"] == str(report_id)

    app.dependency_overrides.pop(get_current_user, None)


def test_admin_analytics_success(monkeypatch):
    app.dependency_overrides[get_current_admin] = lambda: FakeUser(role="admin")

    monkeypatch.setattr(
        AdminService,
        "get_analytics",
        lambda db: {
            "success": True,
            "data": {
                "total_users": 100,
                "total_tracks": 200,
                "total_comments": 50,
                "total_reports": 10,
                "open_reports": 4,
                "under_review_reports": 2,
                "resolved_reports": 3,
                "dismissed_reports": 1,
                "suspended_users": 5,
                "active_streams_today": 24,
            },
        },
    )

    response = client.get("/admin/analytics")

    assert response.status_code == 200
    assert response.json()["data"]["total_users"] == 100

    app.dependency_overrides.pop(get_current_admin, None)


def test_list_reports_success(monkeypatch):
    app.dependency_overrides[get_current_admin] = lambda: FakeUser(role="admin")

    monkeypatch.setattr(
        AdminService,
        "list_reports",
        lambda db, report_status=None, entity_type=None, limit=20, offset=0: {
            "success": True,
            "data": {
                "total": 1,
                "reports": [
                    {
                        "report_id": str(uuid4()),
                        "entity_type": "comment",
                        "entity_id": str(uuid4()),
                        "reason": "Abusive language",
                        "status": "open",
                        "created_at": "2026-04-28T19:00:00+00:00",
                        "reporter": {
                            "user_id": str(uuid4()),
                            "username": "reporter",
                            "display_name": "Reporter",
                        },
                        "reviewed_by": None,
                        "reviewed_at": None,
                        "resolution_note": None,
                        "entity_preview": {
                            "comment_id": str(uuid4()),
                            "content": "Bad comment",
                        },
                    }
                ],
            },
        },
    )

    response = client.get("/admin/reports?status=open")

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1

    app.dependency_overrides.pop(get_current_admin, None)


def test_review_report_success(monkeypatch):
    app.dependency_overrides[get_current_admin] = lambda: FakeUser(role="admin")

    report_id = uuid4()

    monkeypatch.setattr(
        AdminService,
        "review_report",
        lambda db, rid, current_admin, data: {
            "success": True,
            "message": "Report updated successfully.",
            "data": {
                "report_id": str(rid),
                "entity_type": "user",
                "entity_id": str(uuid4()),
                "reason": "Harassment",
                "status": data.status,
                "created_at": "2026-04-28T19:00:00+00:00",
                "reporter": {
                    "user_id": str(uuid4()),
                    "username": "reporter",
                    "display_name": "Reporter",
                },
                "reviewed_by": {
                    "user_id": str(uuid4()),
                    "username": "admin1",
                    "display_name": "Admin One",
                },
                "reviewed_at": "2026-04-28T20:00:00+00:00",
                "resolution_note": data.resolution_note,
                "entity_preview": {
                    "user_id": str(uuid4()),
                    "username": "reported-user",
                    "display_name": "Reported User",
                },
            },
        },
    )

    response = client.patch(
        f"/admin/reports/{report_id}",
        json={
            "status": "resolved",
            "resolution_note": "Confirmed and handled",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "resolved"

    app.dependency_overrides.pop(get_current_admin, None)


def test_update_user_suspension_success(monkeypatch):
    app.dependency_overrides[get_current_admin] = lambda: FakeUser(role="admin")

    user_id = uuid4()

    monkeypatch.setattr(
        AdminService,
        "update_user_suspension",
        lambda db, uid, current_admin, data: {
            "success": True,
            "message": "User suspended successfully.",
            "data": {
                "user_id": str(uid),
                "username": "target",
                "display_name": "Target User",
                "is_suspended": data.is_suspended,
                "reason": data.reason,
            },
        },
    )

    response = client.patch(
        f"/admin/users/{user_id}/suspension",
        json={"is_suspended": True, "reason": "Repeated abuse"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["is_suspended"] is True

    app.dependency_overrides.pop(get_current_admin, None)


def test_delete_comment_success(monkeypatch):
    app.dependency_overrides[get_current_admin] = lambda: FakeUser(role="admin")

    comment_id = uuid4()

    monkeypatch.setattr(
        AdminService,
        "delete_comment",
        lambda db, cid: {
            "success": True,
            "message": "Comment deleted successfully.",
        },
    )

    response = client.delete(f"/admin/comments/{comment_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Comment deleted successfully."

    app.dependency_overrides.pop(get_current_admin, None)


def test_delete_track_success(monkeypatch):
    app.dependency_overrides[get_current_admin] = lambda: FakeUser(role="admin")

    track_id = uuid4()

    monkeypatch.setattr(
        AdminService,
        "delete_track",
        lambda db, tid: {
            "success": True,
            "message": "Track deleted successfully.",
            "data": {
                "track_id": str(tid),
                "title": "Removed Track",
            },
        },
    )

    response = client.delete(f"/admin/tracks/{track_id}")

    assert response.status_code == 200
    assert response.json()["data"]["track_id"] == str(track_id)

    app.dependency_overrides.pop(get_current_admin, None)


def test_update_user_role_success(monkeypatch):
    app.dependency_overrides[get_current_admin] = lambda: FakeUser(role="admin")

    user_id = uuid4()

    monkeypatch.setattr(
        AdminService,
        "update_user_role",
        lambda db, uid, current_admin, data: {
            "success": True,
            "message": "User role updated successfully.",
            "data": {
                "user_id": str(uid),
                "username": "futureadmin",
                "display_name": "Future Admin",
                "role": data.role,
            },
        },
    )

    response = client.patch(
        f"/admin/users/{user_id}/role",
        json={"role": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "admin"

    app.dependency_overrides.pop(get_current_admin, None)

"""HTTP-level tests for /notifications/* endpoints.

Strict status codes settled per service contract:
  - mark read on other user's notif    -> 403 (NotificationService raises 403)
  - delete other user's notif          -> 403
  - mark read on missing notif         -> 404
  - delete missing notif               -> 404
  - listing without auth               -> 401
  - pagination invalid bounds          -> 422 (limit=0/101, offset=-1)
  - mark-all-read called twice         -> idempotent (200 both times)
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from app.services.notification_service import NotificationService


def test_list_notifications_success(client, override_auth, monkeypatch):
    override_auth()
    notif_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    monkeypatch.setattr(
        NotificationService,
        "get_notifications",
        lambda db, user, limit=50, offset=0: {
            "success": True,
            "data": {
                "notifications": [
                    {
                        "notification_id": str(notif_id),
                        "actor_id": str(actor_id),
                        "notification_type": "follow",
                        "target_id": None,
                        "message": "Bob followed you",
                        "is_read": False,
                        "created_at": None,
                    }
                ]
            },
        },
    )

    response = client.get("/notifications")
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]["notifications"]) == 1


def test_list_notifications_without_auth_returns_401(client):
    response = client.get("/notifications")
    assert response.status_code == 401


def test_list_notifications_limit_too_small_returns_422(client, override_auth):
    override_auth()
    response = client.get("/notifications?limit=0")
    assert response.status_code == 422


def test_list_notifications_limit_too_large_returns_422(client, override_auth):
    override_auth()
    response = client.get("/notifications?limit=101")
    assert response.status_code == 422


def test_list_notifications_negative_offset_returns_422(client, override_auth):
    override_auth()
    response = client.get("/notifications?offset=-1")
    assert response.status_code == 422


def test_unread_count_returns_count(client, override_auth, monkeypatch):
    override_auth()
    monkeypatch.setattr(
        NotificationService,
        "get_unread_count",
        lambda db, user: {"success": True, "data": {"unread_count": 3}},
    )

    response = client.get("/notifications/unread-count")
    assert response.status_code == 200
    assert response.json()["data"]["unread_count"] == 3


def test_mark_as_read_success(client, override_auth, monkeypatch):
    override_auth()
    notif_id = uuid.uuid4()

    monkeypatch.setattr(
        NotificationService,
        "mark_as_read",
        lambda db, user, nid: {
            "success": True,
            "message": "Notification marked as read.",
            "data": {"notification_id": str(notif_id), "is_read": True},
        },
    )

    response = client.put(f"/notifications/{notif_id}/read")
    assert response.status_code == 200
    assert response.json()["data"]["is_read"] is True


def test_mark_other_user_notif_as_read_returns_403(
    client, override_auth, monkeypatch
):
    override_auth()
    notif_id = uuid.uuid4()

    def fake_mark(db, user, nid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark your own notifications as read.",
        )

    monkeypatch.setattr(NotificationService, "mark_as_read", fake_mark)

    response = client.put(f"/notifications/{notif_id}/read")
    assert response.status_code == 403


def test_mark_missing_notif_as_read_returns_404(client, override_auth, monkeypatch):
    override_auth()
    notif_id = uuid.uuid4()

    def fake_mark(db, user, nid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    monkeypatch.setattr(NotificationService, "mark_as_read", fake_mark)

    response = client.put(f"/notifications/{notif_id}/read")
    assert response.status_code == 404


def test_delete_other_user_notif_returns_403(client, override_auth, monkeypatch):
    override_auth()
    notif_id = uuid.uuid4()

    def fake_delete(db, user, nid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own notifications.",
        )

    monkeypatch.setattr(NotificationService, "delete_notification", fake_delete)

    response = client.delete(f"/notifications/{notif_id}")
    assert response.status_code == 403


def test_delete_missing_notif_returns_404(client, override_auth, monkeypatch):
    override_auth()
    notif_id = uuid.uuid4()

    def fake_delete(db, user, nid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    monkeypatch.setattr(NotificationService, "delete_notification", fake_delete)

    response = client.delete(f"/notifications/{notif_id}")
    assert response.status_code == 404


def test_mark_all_read_is_idempotent(client, override_auth, monkeypatch):
    """Calling read-all twice should be safe; second call still 200."""
    override_auth()

    call_log = {"n": 0, "marked_first": 5, "marked_second": 0}

    def fake_mark_all(db, user):
        call_log["n"] += 1
        marked = call_log["marked_first"] if call_log["n"] == 1 else call_log[
            "marked_second"
        ]
        return {
            "success": True,
            "message": f"{marked} notification(s) marked as read.",
            "data": {"marked_read": marked},
        }

    monkeypatch.setattr(NotificationService, "mark_all_as_read", fake_mark_all)

    first = client.put("/notifications/read-all")
    second = client.put("/notifications/read-all")

    assert first.status_code == 200
    assert first.json()["data"]["marked_read"] == 5

    assert second.status_code == 200
    assert second.json()["data"]["marked_read"] == 0
    assert call_log["n"] == 2

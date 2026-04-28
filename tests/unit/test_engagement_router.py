from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.dependencies import get_db, get_optional_current_user
from app.main import app
from app.services.engagement_service import EngagementService

client = TestClient(app)


class FakeUser:
    def __init__(self, user_id):
        self.user_id = user_id


class DummyDB:
    pass


def override_get_db():
    yield DummyDB()


def setup_module(module):
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(module):
    app.dependency_overrides.clear()


def test_get_track_like_count_endpoint_success(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        EngagementService,
        "get_track_like_count",
        lambda db, tid, current_user=None: {
            "success": True,
            "data": {
                "track_id": str(track_id),
                "like_count": 12,
            },
        },
    )

    response = client.get(f"/tracks/{track_id}/likes/count")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["track_id"] == str(track_id)
    assert body["data"]["like_count"] == 12


def test_get_track_like_count_endpoint_passes_optional_user(monkeypatch):
    track_id = uuid4()
    current_user = FakeUser(uuid4())
    seen_user_ids = []

    app.dependency_overrides[get_optional_current_user] = lambda: current_user

    def fake_get_track_like_count(db, tid, current_user=None):
        seen_user_ids.append(current_user.user_id if current_user else None)
        return {
            "success": True,
            "data": {
                "track_id": str(tid),
                "like_count": 1,
            },
        }

    monkeypatch.setattr(
        EngagementService,
        "get_track_like_count",
        fake_get_track_like_count,
    )

    response = client.get(f"/tracks/{track_id}/likes/count")

    assert response.status_code == 200
    assert seen_user_ids == [current_user.user_id]

    app.dependency_overrides.pop(get_optional_current_user, None)


def test_get_track_like_count_endpoint_private_track_forbidden(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        EngagementService,
        "get_track_like_count",
        lambda db, tid, current_user=None: (_ for _ in ()).throw(
            HTTPException(status_code=403, detail="Track is private.")
        ),
    )

    response = client.get(f"/tracks/{track_id}/likes/count")

    assert response.status_code == 403
    assert response.json()["detail"] == "Track is private."


def test_get_track_engagement_summary_endpoint_success(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        EngagementService,
        "get_track_engagement_summary",
        lambda db, tid, current_user=None: {
            "success": True,
            "data": {
                "track_id": str(track_id),
                "like_count": 12,
                "comment_count": 3,
                "repost_count": 2,
                "liked_by_me": None,
                "reposted_by_me": None,
            },
        },
    )

    response = client.get(f"/tracks/{track_id}/engagement-summary")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["track_id"] == str(track_id)
    assert body["data"]["like_count"] == 12
    assert body["data"]["comment_count"] == 3
    assert body["data"]["repost_count"] == 2
    assert body["data"]["liked_by_me"] is None
    assert body["data"]["reposted_by_me"] is None


def test_get_track_engagement_summary_endpoint_passes_optional_user(monkeypatch):
    track_id = uuid4()
    current_user = FakeUser(uuid4())
    seen_user_ids = []

    app.dependency_overrides[get_optional_current_user] = lambda: current_user

    def fake_get_track_engagement_summary(db, tid, current_user=None):
        seen_user_ids.append(current_user.user_id if current_user else None)
        return {
            "success": True,
            "data": {
                "track_id": str(tid),
                "like_count": 1,
                "comment_count": 0,
                "repost_count": 0,
                "liked_by_me": True,
                "reposted_by_me": False,
            },
        }

    monkeypatch.setattr(
        EngagementService,
        "get_track_engagement_summary",
        fake_get_track_engagement_summary,
    )

    response = client.get(f"/tracks/{track_id}/engagement-summary")

    assert response.status_code == 200
    assert seen_user_ids == [current_user.user_id]

    app.dependency_overrides.pop(get_optional_current_user, None)


def test_get_track_engagement_summary_endpoint_private_track_forbidden(monkeypatch):
    track_id = uuid4()

    monkeypatch.setattr(
        EngagementService,
        "get_track_engagement_summary",
        lambda db, tid, current_user=None: (_ for _ in ()).throw(
            HTTPException(status_code=403, detail="Track is private.")
        ),
    )

    response = client.get(f"/tracks/{track_id}/engagement-summary")

    assert response.status_code == 403
    assert response.json()["detail"] == "Track is private."

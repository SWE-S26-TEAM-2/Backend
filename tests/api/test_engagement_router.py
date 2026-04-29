"""HTTP-level tests for the (newly mounted) engagement router.

Covers likes/reposts/comments routes that exist in
``app.routers.engagement`` and were previously not wired into ``main.py``.

Service contract (see ``EngagementService``):
  - like a track twice -> 400 (NOT 200/409). The audit asked us to settle
    on 200 vs 409; the actual contract today is 400 ("already liked").
  - repost track twice -> 400 ("already reposted").
  - unlike when not liked -> 400.
  - target track missing -> 404.
  - comment ``content`` length: 1..500 chars (Pydantic Field).

Note on "delete other user's comment" from the audit plan: the engagement
router does not currently expose a DELETE /comments endpoint, so we only
assert status codes for the routes that actually exist. See the
unresolved TODOs section in the parent task summary.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from app.services.engagement_service import EngagementService


# ── Likes ────────────────────────────────────────────────


def test_like_track_success(client, override_auth, monkeypatch):
    override_auth()
    track_id = uuid.uuid4()
    like_id = uuid.uuid4()

    monkeypatch.setattr(
        EngagementService,
        "like_track",
        lambda db, user, tid: {
            "success": True,
            "message": "Track liked.",
            "data": {"like_id": str(like_id), "track_id": str(tid)},
        },
    )

    response = client.post(f"/likes/tracks/{track_id}")
    assert response.status_code == 200
    assert response.json()["data"]["track_id"] == str(track_id)


def test_like_track_idempotent_second_call_returns_400(
    client, override_auth, monkeypatch
):
    """Second like raises 400 ("already liked"); the contract is pinned."""
    override_auth()
    track_id = uuid.uuid4()
    state = {"liked": False}

    def fake_like(db, user, tid):
        if state["liked"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already liked this track.",
            )
        state["liked"] = True
        return {
            "success": True,
            "message": "Track liked.",
            "data": {"like_id": str(uuid.uuid4()), "track_id": str(tid)},
        }

    monkeypatch.setattr(EngagementService, "like_track", fake_like)

    first = client.post(f"/likes/tracks/{track_id}")
    second = client.post(f"/likes/tracks/{track_id}")

    assert first.status_code == 200
    assert second.status_code == 400


def test_unlike_track_success(client, override_auth, monkeypatch):
    override_auth()
    track_id = uuid.uuid4()

    monkeypatch.setattr(
        EngagementService,
        "unlike_track",
        lambda db, user, tid: {
            "success": True,
            "message": "Track unliked.",
        },
    )

    response = client.delete(f"/likes/tracks/{track_id}")
    assert response.status_code == 200


def test_unlike_when_not_liked_returns_400(client, override_auth, monkeypatch):
    override_auth()
    track_id = uuid.uuid4()

    def fake_unlike(db, user, tid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have not liked this track.",
        )

    monkeypatch.setattr(EngagementService, "unlike_track", fake_unlike)

    response = client.delete(f"/likes/tracks/{track_id}")
    assert response.status_code == 400


def test_like_track_missing_track_returns_404(client, override_auth, monkeypatch):
    override_auth()
    track_id = uuid.uuid4()

    def fake_like(db, user, tid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found.",
        )

    monkeypatch.setattr(EngagementService, "like_track", fake_like)

    response = client.post(f"/likes/tracks/{track_id}")
    assert response.status_code == 404


def test_like_track_without_auth_returns_401(client):
    track_id = uuid.uuid4()
    response = client.post(f"/likes/tracks/{track_id}")
    assert response.status_code == 401


# ── Reposts ──────────────────────────────────────────────


def test_repost_track_success(client, override_auth, monkeypatch):
    override_auth()
    track_id = uuid.uuid4()
    repost_id = uuid.uuid4()

    monkeypatch.setattr(
        EngagementService,
        "repost_track",
        lambda db, user, tid: {
            "success": True,
            "message": "Track reposted.",
            "data": {"repost_id": str(repost_id), "track_id": str(tid)},
        },
    )

    response = client.post(f"/reposts/tracks/{track_id}")
    assert response.status_code == 200
    assert response.json()["data"]["repost_id"] == str(repost_id)


def test_remove_repost_success(client, override_auth, monkeypatch):
    override_auth()
    track_id = uuid.uuid4()

    monkeypatch.setattr(
        EngagementService,
        "remove_repost",
        lambda db, user, tid: {
            "success": True,
            "message": "Repost removed.",
        },
    )

    response = client.delete(f"/reposts/tracks/{track_id}")
    assert response.status_code == 200


def test_double_repost_returns_400(client, override_auth, monkeypatch):
    override_auth()
    track_id = uuid.uuid4()

    def fake_repost(db, user, tid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already reposted this track.",
        )

    monkeypatch.setattr(EngagementService, "repost_track", fake_repost)

    response = client.post(f"/reposts/tracks/{track_id}")
    assert response.status_code == 400


# ── Comments ─────────────────────────────────────────────


def test_get_comments_returns_list(client, monkeypatch):
    track_id = uuid.uuid4()
    comment_id = uuid.uuid4()
    user_id = uuid.uuid4()

    monkeypatch.setattr(
        EngagementService,
        "get_track_comments",
        lambda db, tid, limit=50, offset=0, current_user=None: {
            "success": True,
            "data": {
                "comments": [
                    {
                        "comment_id": str(comment_id),
                        "user_id": str(user_id),
                        "content": "great track",
                        "timestamp_in_track": 12,
                        "parent_comment_id": None,
                        "created_at": None,
                    }
                ]
            },
        },
    )

    response = client.get(f"/tracks/{track_id}/comments")
    assert response.status_code == 200
    assert len(response.json()["data"]["comments"]) == 1


def test_get_comments_pagination_limit_too_large_returns_422(client):
    track_id = uuid.uuid4()
    response = client.get(f"/tracks/{track_id}/comments?limit=101")
    assert response.status_code == 422


def test_get_comments_pagination_negative_offset_returns_422(client):
    track_id = uuid.uuid4()
    response = client.get(f"/tracks/{track_id}/comments?offset=-1")
    assert response.status_code == 422


def test_add_comment_success(client, override_auth, monkeypatch):
    override_auth()
    track_id = uuid.uuid4()
    comment_id = uuid.uuid4()

    def fake_add(db, user, tid, data):
        return {
            "success": True,
            "message": "Comment added.",
            "data": {
                "comment_id": str(comment_id),
                "track_id": str(tid),
                "content": data.content,
                "timestamp_in_track": data.timestamp_in_track,
                "parent_comment_id": None,
                "created_at": None,
            },
        }

    monkeypatch.setattr(EngagementService, "add_comment", fake_add)

    response = client.post(
        f"/tracks/{track_id}/comments",
        json={"content": "Loved this!", "timestamp_in_track": 30},
    )
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "Loved this!"


def test_add_comment_empty_content_returns_422(client, override_auth):
    override_auth()
    track_id = uuid.uuid4()
    response = client.post(
        f"/tracks/{track_id}/comments", json={"content": ""}
    )
    assert response.status_code == 422


def test_add_comment_too_long_content_returns_422(client, override_auth):
    override_auth()
    track_id = uuid.uuid4()
    response = client.post(
        f"/tracks/{track_id}/comments", json={"content": "x" * 501}
    )
    assert response.status_code == 422


def test_add_comment_max_length_500_succeeds(
    client, override_auth, monkeypatch
):
    override_auth()
    track_id = uuid.uuid4()

    def fake_add(db, user, tid, data):
        assert len(data.content) == 500
        return {
            "success": True,
            "message": "Comment added.",
            "data": {
                "comment_id": str(uuid.uuid4()),
                "track_id": str(tid),
                "content": data.content,
                "timestamp_in_track": None,
                "parent_comment_id": None,
                "created_at": None,
            },
        }

    monkeypatch.setattr(EngagementService, "add_comment", fake_add)

    response = client.post(
        f"/tracks/{track_id}/comments", json={"content": "x" * 500}
    )
    assert response.status_code == 200


def test_add_comment_without_auth_returns_401(client):
    track_id = uuid.uuid4()
    response = client.post(
        f"/tracks/{track_id}/comments", json={"content": "hi"}
    )
    assert response.status_code == 401


# TODO clarify auth contract: the engagement router does not currently
# expose DELETE /comments/{id}, so the audit's "delete other user's
# comment 403/404" cannot be tested at the HTTP layer. Surfaced as an
# unresolved TODO in the parent task summary.

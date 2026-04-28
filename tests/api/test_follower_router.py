"""HTTP-level tests for /users/{username}/follow and /users/{username}/block.

Strict status codes settled per service contract:
  - follow self           -> 400 (FollowerService raises 400)
  - follow unknown        -> 404
  - double-follow         -> 400 (NOT 409 – service raises 400, see
                            FollowerService.follow_user)
  - unfollow when not following -> 404
  - block self            -> 400
  - block unknown         -> 404
  - missing auth          -> 401
  - private profile follow -> service still allows the follow itself; the
                              private flag affects /followers visibility.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from app.services.block_service import BlockService
from app.services.follower_service import FollowerService


# ── Follow ───────────────────────────────────────────────


def test_follow_user_success(client, override_auth, monkeypatch):
    me = override_auth()

    def fake_follow(db, current_user, username):
        assert current_user.user_id == me.user_id
        assert username == "alice"
        return {"success": True, "message": "You are now following Alice."}

    monkeypatch.setattr(FollowerService, "follow_user", fake_follow)

    response = client.post("/users/alice/follow")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_follow_self_returns_400(client, override_auth, monkeypatch):
    override_auth()

    def fake_follow(db, current_user, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself.",
        )

    monkeypatch.setattr(FollowerService, "follow_user", fake_follow)

    response = client.post("/users/me_self/follow")
    assert response.status_code == 400


def test_follow_unknown_user_returns_404(client, override_auth, monkeypatch):
    override_auth()

    def fake_follow(db, current_user, username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    monkeypatch.setattr(FollowerService, "follow_user", fake_follow)

    response = client.post("/users/ghost/follow")
    assert response.status_code == 404


def test_double_follow_returns_400(client, override_auth, monkeypatch):
    """Service raises 400 (not 409) when an existing follow row is found."""
    override_auth()

    def fake_follow(db, current_user, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already following Alice.",
        )

    monkeypatch.setattr(FollowerService, "follow_user", fake_follow)

    response = client.post("/users/alice/follow")
    assert response.status_code == 400


def test_follow_missing_auth_returns_401(client):
    response = client.post("/users/alice/follow")
    assert response.status_code == 401


# ── Unfollow ─────────────────────────────────────────────


def test_unfollow_success(client, override_auth, monkeypatch):
    override_auth()
    monkeypatch.setattr(
        FollowerService,
        "unfollow_user",
        lambda db, user, username: {
            "success": True,
            "message": "Successfully unfollowed.",
        },
    )

    response = client.delete("/users/alice/follow")
    assert response.status_code == 200


def test_unfollow_when_not_following_returns_404(client, override_auth, monkeypatch):
    override_auth()

    def fake_unfollow(db, user, username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not following this user.",
        )

    monkeypatch.setattr(FollowerService, "unfollow_user", fake_unfollow)

    response = client.delete("/users/alice/follow")
    assert response.status_code == 404


# ── Block / Unblock ──────────────────────────────────────


def test_block_user_success(client, override_auth, monkeypatch):
    override_auth()
    monkeypatch.setattr(
        BlockService,
        "block_user",
        lambda db, user, username: {
            "success": True,
            "message": "User blocked successfully.",
        },
    )

    response = client.post("/users/alice/block")
    assert response.status_code == 200


def test_block_self_returns_400(client, override_auth, monkeypatch):
    override_auth()

    def fake_block(db, user, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot block yourself.",
        )

    monkeypatch.setattr(BlockService, "block_user", fake_block)

    response = client.post("/users/me_self/block")
    assert response.status_code == 400


def test_block_unknown_returns_404(client, override_auth, monkeypatch):
    override_auth()

    def fake_block(db, user, username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    monkeypatch.setattr(BlockService, "block_user", fake_block)

    response = client.post("/users/ghost/block")
    assert response.status_code == 404


def test_unblock_when_not_blocked_returns_404(client, override_auth, monkeypatch):
    override_auth()

    def fake_unblock(db, user, username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not blocked this user.",
        )

    monkeypatch.setattr(BlockService, "unblock_user", fake_unblock)

    response = client.delete("/users/alice/block")
    assert response.status_code == 404


# ── List followers / following ───────────────────────────


def test_get_my_followers_returns_list(client, override_auth, monkeypatch):
    me = override_auth()
    follower_id = uuid.uuid4()

    monkeypatch.setattr(
        FollowerService,
        "get_my_followers",
        lambda db, user: {
            "success": True,
            "data": {
                "count": 1,
                "followers": [
                    {
                        "user_id": str(follower_id),
                        "display_name": "Bob",
                        "profile_picture": None,
                        "followed_at": None,
                    }
                ],
            },
        },
    )

    response = client.get("/users/me/followers")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["count"] == 1
    assert len(body["data"]["followers"]) == 1
    assert me.user_id  # silence linter


def test_private_profile_followers_list_returns_private_marker(
    client, override_auth, monkeypatch
):
    override_auth()

    monkeypatch.setattr(
        FollowerService,
        "get_user_followers_by_username",
        lambda db, username: {
            "success": True,
            "data": {
                "count": 5,
                "followers": [],
                "private": True,
            },
        },
    )

    response = client.get("/users/secretive/followers")
    assert response.status_code == 200
    assert response.json()["data"]["private"] is True


# ── List endpoints require auth ──────────────────────────


def test_get_my_followers_without_auth_returns_401(client):
    response = client.get("/users/me/followers")
    assert response.status_code == 401


def test_get_user_following_without_auth_returns_401(client):
    """Listing other users' following also requires auth (current contract)."""
    response = client.get("/users/alice/following")
    assert response.status_code == 401

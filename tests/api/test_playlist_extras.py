"""HTTP-level tests for playlist features missing from tests/unit:

  - GET /playlists/liked
  - POST /playlists/{id}/like
  - DELETE /playlists/{id}/like
  - POST /playlists/{id}/cover (multipart)
  - 403 when editing another user's playlist
  - idempotent like (second like returns 400 per service contract)

Service contract for double-like:
  ``PlaylistService.like_playlist`` raises 400 ("already liked") on the
  second call, NOT 200/409. The test asserts 400 so the contract is
  pinned. Idempotency is therefore "first 200, subsequent 400" rather
  than "always 200".
"""

from __future__ import annotations

import io
import uuid

from fastapi import HTTPException, status

from app.services.playlist_service import PlaylistService


def test_get_liked_playlists_returns_200(client, override_auth, monkeypatch):
    override_auth()
    monkeypatch.setattr(
        PlaylistService,
        "get_liked_playlists",
        lambda db, user: {"success": True, "data": []},
    )

    response = client.get("/playlists/liked")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_liked_playlists_without_auth_returns_401(client):
    response = client.get("/playlists/liked")
    assert response.status_code == 401


def test_like_playlist_success(client, override_auth, monkeypatch):
    override_auth()
    playlist_id = uuid.uuid4()
    like_id = uuid.uuid4()

    monkeypatch.setattr(
        PlaylistService,
        "like_playlist",
        lambda db, user, pid: {
            "success": True,
            "message": "Playlist liked successfully.",
            "data": {
                "playlist_like_id": str(like_id),
                "playlist_id": str(pid),
            },
        },
    )

    response = client.post(f"/playlists/{playlist_id}/like")
    assert response.status_code == 200
    assert response.json()["data"]["playlist_id"] == str(playlist_id)


def test_like_playlist_idempotent_second_call_returns_400(
    client, override_auth, monkeypatch
):
    """Service raises 400 on the second like ("already liked").

    The audit suggested either 200 or 409 should be settled; the current
    contract is 400. We pin the contract here.
    """
    override_auth()
    playlist_id = uuid.uuid4()
    state = {"liked": False}

    def fake_like(db, user, pid):
        if state["liked"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already liked this playlist",
            )
        state["liked"] = True
        return {
            "success": True,
            "message": "Playlist liked successfully.",
            "data": {
                "playlist_like_id": str(uuid.uuid4()),
                "playlist_id": str(pid),
            },
        }

    monkeypatch.setattr(PlaylistService, "like_playlist", fake_like)

    first = client.post(f"/playlists/{playlist_id}/like")
    second = client.post(f"/playlists/{playlist_id}/like")

    assert first.status_code == 200
    assert second.status_code == 400


def test_unlike_playlist_success(client, override_auth, monkeypatch):
    override_auth()
    playlist_id = uuid.uuid4()

    monkeypatch.setattr(
        PlaylistService,
        "unlike_playlist",
        lambda db, user, pid: {
            "success": True,
            "message": "Playlist unliked successfully.",
        },
    )

    response = client.delete(f"/playlists/{playlist_id}/like")
    assert response.status_code == 200


def test_unlike_when_not_liked_returns_400(client, override_auth, monkeypatch):
    override_auth()
    playlist_id = uuid.uuid4()

    def fake_unlike(db, user, pid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have not liked this playlist",
        )

    monkeypatch.setattr(PlaylistService, "unlike_playlist", fake_unlike)

    response = client.delete(f"/playlists/{playlist_id}/like")
    assert response.status_code == 400


def test_upload_cover_photo_success(client, override_auth, monkeypatch):
    override_auth()
    playlist_id = uuid.uuid4()
    cover_url = f"/api/uploads/playlist_{playlist_id}.jpg"

    monkeypatch.setattr(
        PlaylistService,
        "upload_cover_photo",
        lambda db, user, pid, file: {
            "success": True,
            "message": "Cover photo uploaded successfully.",
            "data": {
                "playlist_id": str(pid),
                "cover_photo_url": cover_url,
            },
        },
    )

    file_content = b"fakeimagebytes"
    response = client.post(
        f"/playlists/{playlist_id}/cover",
        files={"file": ("cover.jpg", io.BytesIO(file_content), "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["data"]["cover_photo_url"] == cover_url


def test_upload_cover_photo_other_user_returns_403(
    client, override_auth, monkeypatch
):
    override_auth()
    playlist_id = uuid.uuid4()

    def fake_upload(db, user, pid, file):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload cover photos for your own playlists",
        )

    monkeypatch.setattr(PlaylistService, "upload_cover_photo", fake_upload)

    response = client.post(
        f"/playlists/{playlist_id}/cover",
        files={"file": ("c.jpg", io.BytesIO(b"x"), "image/jpeg")},
    )
    assert response.status_code == 403


def test_update_other_users_playlist_returns_403(
    client, override_auth, monkeypatch
):
    override_auth()
    playlist_id = uuid.uuid4()

    def fake_update(db, user, pid, data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own playlists",
        )

    monkeypatch.setattr(PlaylistService, "update_playlist", fake_update)

    response = client.patch(
        f"/playlists/{playlist_id}", json={"name": "Hijacked"}
    )
    assert response.status_code == 403


def test_delete_other_users_playlist_returns_403(
    client, override_auth, monkeypatch
):
    override_auth()
    playlist_id = uuid.uuid4()

    def fake_delete(db, user, pid):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own playlists",
        )

    monkeypatch.setattr(PlaylistService, "delete_playlist", fake_delete)

    response = client.delete(f"/playlists/{playlist_id}")
    assert response.status_code == 403

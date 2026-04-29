"""HTTP-level oversize-upload contract tests.

Service contracts (updated — BE-007 fixed):
  - ``track_service.TRACK_MAX_SIZE``       = 100 MB; oversize -> HTTP 413
  - ``track_service.COVER_IMAGE_MAX_SIZE`` =  10 MB; oversize -> HTTP 413
  - ``user_service.AVATAR_MAX_SIZE``       =   5 MB; oversize -> HTTP 413
  - ``user_service.COVER_MAX_SIZE``        =  10 MB; oversize -> HTTP 413

Speed: the production constants are 5-100 MB which is too expensive to
materialise per test. Each test below temporarily monkeypatches the
constant down to a tiny value (``_SMALL_LIMIT``) so the upload buffer is
``_SMALL_LIMIT + 1`` bytes, while still verifying the same code path.
"""

from __future__ import annotations

import io
import os

import pytest

from app.services import track_service, user_service


# A small budget (4 KiB) is plenty larger than 0 yet cheap to allocate.
_SMALL_LIMIT = 4 * 1024







def _oversize_buffer(limit_bytes: int) -> io.BytesIO:
    return io.BytesIO(b"\0" * (limit_bytes + 1))


@pytest.fixture
def shrunk_track_limits(monkeypatch):
    """Lower TRACK_MAX_SIZE / COVER_IMAGE_MAX_SIZE for the test."""
    monkeypatch.setattr(track_service, "TRACK_MAX_SIZE", _SMALL_LIMIT, raising=False)
    monkeypatch.setattr(
        track_service, "COVER_IMAGE_MAX_SIZE", _SMALL_LIMIT, raising=False
    )
    return _SMALL_LIMIT


@pytest.fixture
def shrunk_user_limits(monkeypatch):
    """Lower AVATAR_MAX_SIZE / COVER_MAX_SIZE for the test."""
    monkeypatch.setattr(user_service, "AVATAR_MAX_SIZE", _SMALL_LIMIT, raising=False)
    monkeypatch.setattr(user_service, "COVER_MAX_SIZE", _SMALL_LIMIT, raising=False)
    return _SMALL_LIMIT


# ── Track upload (POST /tracks/) ─────────────────────────


def test_track_upload_oversize_returns_413(
    client, override_auth, tmp_upload_dir, shrunk_track_limits
):
    override_auth()

    payload = _oversize_buffer(shrunk_track_limits)

    response = client.post(
        "/tracks/",
        data={"title": "Big", "description": "Too big", "visibility": "public"},
        files={"file": ("huge.mp3", payload, "audio/mpeg")},
    )

    assert response.status_code == 413
    assert "100 MB" in response.json()["detail"]
    assert os.path.isdir(tmp_upload_dir)


def test_track_upload_invalid_content_type_returns_400(
    client, override_auth, tmp_upload_dir
):
    """Non-audio files are rejected before size is even checked (400)."""
    override_auth()

    response = client.post(
        "/tracks/",
        data={"title": "X", "description": "Y", "visibility": "public"},
        files={"file": ("not-audio.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 400


def test_track_cover_oversize_returns_413(
    client, override_auth, tmp_upload_dir, shrunk_track_limits
):
    """Oversize cover image rejected when uploading a track."""
    override_auth()

    audio = io.BytesIO(b"OggS" + b"\0" * 1024)
    big_cover = _oversize_buffer(shrunk_track_limits)

    response = client.post(
        "/tracks/",
        data={"title": "X", "description": "Y", "visibility": "public"},
        files={
            "file": ("song.ogg", audio, "audio/ogg"),
            "cover_image": ("cover.jpg", big_cover, "image/jpeg"),
        },
    )

    assert response.status_code == 413
    assert "10 MB" in response.json()["detail"]


# ── Avatar upload (PUT /users/me/avatar) ─────────────────


def test_avatar_oversize_returns_413(
    client, override_auth, tmp_upload_dir, shrunk_user_limits
):
    override_auth()

    big_avatar = _oversize_buffer(shrunk_user_limits)

    response = client.put(
        "/users/me/avatar",
        files={"file": ("avatar.jpg", big_avatar, "image/jpeg")},
    )

    assert response.status_code == 413
    assert "5 MB" in response.json()["detail"]


def test_avatar_invalid_type_returns_400(client, override_auth, tmp_upload_dir):
    override_auth()

    response = client.put(
        "/users/me/avatar",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
    )

    assert response.status_code == 400


# ── Cover photo upload (PUT /users/me/cover) ─────────────


def test_user_cover_oversize_returns_413(
    client, override_auth, tmp_upload_dir, shrunk_user_limits
):
    override_auth()

    big_cover = _oversize_buffer(shrunk_user_limits)

    response = client.put(
        "/users/me/cover",
        files={"file": ("cover.jpg", big_cover, "image/jpeg")},
    )

    assert response.status_code == 413
    assert "10 MB" in response.json()["detail"]


# ── Auth-mode strictness ─────────────────────────────────


def test_track_upload_without_auth_returns_401(client, tmp_upload_dir):
    response = client.post(
        "/tracks/",
        data={"title": "X", "description": "Y", "visibility": "public"},
        files={"file": ("song.mp3", io.BytesIO(b"\0\0\0"), "audio/mpeg")},
    )
    assert response.status_code == 401


def test_avatar_upload_without_auth_returns_401(client, tmp_upload_dir):
    response = client.put(
        "/users/me/avatar",
        files={"file": ("avatar.jpg", io.BytesIO(b"\0"), "image/jpeg")},
    )
    assert response.status_code == 401

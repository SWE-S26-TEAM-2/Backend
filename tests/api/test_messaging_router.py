"""HTTP-level tests for /conversations/* endpoints.

Strict status codes settled per service contract:
  - create with self                     -> 400 (MessagingService raises 400)
  - create with non-existent username    -> 400 (NOT 404; service raises 400
                                                 with detail
                                                 "Invalid participant — user
                                                 does not exist.")
  - send with all-null body              -> 422 (model_validator)
  - send with track-only                 -> 200 (router returns 201 actually,
                                                 router status_code=201)
  - mark read on non-participant         -> 403
  - mark read on missing message         -> 404
  - listing without auth                 -> 401
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from app.services.messaging_service import MessagingService


# ── Create conversation ──────────────────────────────────


def test_create_conversation_with_self_returns_400(
    client, override_auth, monkeypatch
):
    override_auth()

    def fake_create(db, user, data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot start a conversation with yourself.",
        )

    monkeypatch.setattr(
        MessagingService, "create_or_get_conversation", fake_create
    )

    response = client.post("/conversations", json={"username": "myself"})
    assert response.status_code == 400


def test_create_conversation_with_unknown_username_returns_400(
    client, override_auth, monkeypatch
):
    """Service contract: 400 when the participant doesn't exist (not 404)."""
    override_auth()

    def fake_create(db, user, data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid participant — user does not exist.",
        )

    monkeypatch.setattr(
        MessagingService, "create_or_get_conversation", fake_create
    )

    response = client.post("/conversations", json={"username": "ghost"})
    assert response.status_code == 400


def test_create_conversation_success(client, override_auth, monkeypatch):
    override_auth()
    conversation_id = uuid.uuid4()

    monkeypatch.setattr(
        MessagingService,
        "create_or_get_conversation",
        lambda db, user, data: {
            "success": True,
            "data": {"conversation_id": str(conversation_id)},
        },
    )

    response = client.post("/conversations", json={"username": "alice"})
    assert response.status_code == 201
    assert response.json()["data"]["conversation_id"] == str(conversation_id)


def test_create_conversation_missing_username_returns_422(client, override_auth):
    override_auth()
    response = client.post("/conversations", json={})
    assert response.status_code == 422


def test_create_conversation_without_auth_returns_401(client):
    response = client.post("/conversations", json={"username": "alice"})
    assert response.status_code == 401


# ── Send message validation ──────────────────────────────


def test_send_message_with_all_null_body_returns_422(client, override_auth):
    """Schema model_validator rejects empty content/track_id/playlist_id."""
    override_auth()
    conversation_id = uuid.uuid4()

    response = client.post(
        f"/conversations/{conversation_id}/messages", json={}
    )
    assert response.status_code == 422


def test_send_message_with_track_only_succeeds(client, override_auth, monkeypatch):
    me = override_auth()
    conversation_id = uuid.uuid4()
    track_id = uuid.uuid4()
    message_id = uuid.uuid4()
    receiver_id = uuid.uuid4()

    def fake_send(db, user, conv_id, data):
        assert data.track_id is not None
        return {
            "success": True,
            "data": {
                "id": str(message_id),
                "sender_id": str(user.user_id),
                "receiver_id": str(receiver_id),
                "content": None,
                "track_id": str(data.track_id),
                "playlist_id": None,
                "is_read": False,
                "created_at": None,
            },
        }

    monkeypatch.setattr(MessagingService, "send_message", fake_send)

    response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={"track_id": str(track_id)},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["data"]["track_id"] == str(track_id)
    assert body["data"]["sender_id"] == str(me.user_id)


def test_send_message_text_only_succeeds(client, override_auth, monkeypatch):
    override_auth()
    conversation_id = uuid.uuid4()
    message_id = uuid.uuid4()

    monkeypatch.setattr(
        MessagingService,
        "send_message",
        lambda db, user, conv_id, data: {
            "success": True,
            "data": {
                "id": str(message_id),
                "sender_id": str(user.user_id),
                "receiver_id": str(uuid.uuid4()),
                "content": data.content,
                "track_id": None,
                "playlist_id": None,
                "is_read": False,
                "created_at": None,
            },
        },
    )

    response = client.post(
        f"/conversations/{conversation_id}/messages", json={"content": "hi"}
    )
    assert response.status_code == 201


# ── List conversations / unread count ────────────────────


def test_list_conversations_with_auth_returns_200(
    client, override_auth, monkeypatch
):
    override_auth()
    monkeypatch.setattr(
        MessagingService,
        "get_user_conversations",
        lambda db, user: {"success": True, "data": []},
    )

    response = client.get("/conversations")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_list_conversations_without_auth_returns_401(client):
    response = client.get("/conversations")
    assert response.status_code == 401


def test_unread_message_count_returns_count(client, override_auth, monkeypatch):
    override_auth()
    monkeypatch.setattr(
        MessagingService,
        "get_unread_message_count",
        lambda db, user: {"success": True, "data": {"unread_count": 7}},
    )

    response = client.get("/conversations/unread-count")
    assert response.status_code == 200
    assert response.json()["data"]["unread_count"] == 7


# ── Mark read ────────────────────────────────────────────


def test_mark_read_on_non_participant_returns_403(
    client, override_auth, monkeypatch
):
    override_auth()
    conv_id = uuid.uuid4()
    msg_id = uuid.uuid4()

    def fake_mark(db, user, c, m):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this conversation.",
        )

    monkeypatch.setattr(MessagingService, "mark_message_as_read", fake_mark)

    response = client.patch(f"/conversations/{conv_id}/messages/{msg_id}/read")
    assert response.status_code == 403


def test_mark_read_on_missing_conversation_returns_404(
    client, override_auth, monkeypatch
):
    override_auth()
    conv_id = uuid.uuid4()
    msg_id = uuid.uuid4()

    def fake_mark(db, user, c, m):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    monkeypatch.setattr(MessagingService, "mark_message_as_read", fake_mark)

    response = client.patch(f"/conversations/{conv_id}/messages/{msg_id}/read")
    assert response.status_code == 404


def test_mark_read_idempotent_on_already_read(
    client, override_auth, monkeypatch
):
    override_auth()
    conv_id = uuid.uuid4()
    msg_id = uuid.uuid4()

    monkeypatch.setattr(
        MessagingService,
        "mark_message_as_read",
        lambda db, user, c, m: {
            "success": True,
            "message": "Message was already marked as read.",
            "data": {"message_id": str(m), "is_read": True},
        },
    )

    first = client.patch(f"/conversations/{conv_id}/messages/{msg_id}/read")
    second = client.patch(f"/conversations/{conv_id}/messages/{msg_id}/read")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()

"""HTTP-level test for the root health-check endpoint."""

from __future__ import annotations


def test_root_returns_message(client):
    """``GET /`` returns 200 with the expected health message."""
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert body["message"] == "API is running"


def test_root_does_not_require_auth(client):
    """Health check is public – no auth header should still work."""
    response = client.get("/", headers={})
    assert response.status_code == 200

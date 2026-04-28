"""HTTP-level tests for /search/playlists.

Covers the previously-untested third arm of the search router. ``keyword``
is a required query parameter so omitting it must yield a strict 422.
"""

from __future__ import annotations

import uuid

from app.services.search_service import SearchService


def test_search_playlists_with_keyword_returns_200(client, monkeypatch):
    playlist_id = uuid.uuid4()
    user_id = uuid.uuid4()

    def fake_search(db, keyword):
        assert keyword == "summer"
        return {
            "success": True,
            "data": {
                "playlists": [
                    {
                        "playlist_id": str(playlist_id),
                        "user_id": str(user_id),
                        "name": "Summer Vibes",
                        "description": "Hot tunes",
                        "cover_photo_url": None,
                        "tracks": [],
                    }
                ]
            },
        }

    monkeypatch.setattr(SearchService, "search_playlists", fake_search)

    response = client.get("/search/playlists?keyword=summer")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["playlists"]) == 1
    assert body["data"]["playlists"][0]["name"] == "Summer Vibes"


def test_search_playlists_no_results(client, monkeypatch):
    monkeypatch.setattr(
        SearchService,
        "search_playlists",
        lambda db, keyword: {"success": True, "data": {"playlists": []}},
    )

    response = client.get("/search/playlists?keyword=zzz_no_match")
    assert response.status_code == 200
    assert response.json()["data"]["playlists"] == []


def test_search_playlists_missing_keyword_returns_422(client):
    """``keyword`` is required (Query(...)) – omission must be 422, not 400."""
    response = client.get("/search/playlists")
    assert response.status_code == 422


def test_search_playlists_passes_keyword_unchanged(client, monkeypatch):
    received = {}

    def fake_search(db, keyword):
        received["keyword"] = keyword
        return {"success": True, "data": {"playlists": []}}

    monkeypatch.setattr(SearchService, "search_playlists", fake_search)

    client.get("/search/playlists?keyword=Hello%20World")
    assert received["keyword"] == "Hello World"

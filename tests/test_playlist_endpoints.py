import time
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Replace these with a VERIFIED test user that already works in Postman
TEST_EMAIL = "adamamrmoharam@example.com"
TEST_PASSWORD = "adam2005"


def unique_text(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000)}"


def login_and_get_headers() -> dict:
    response = client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 200, response.text

    data = response.json()
    access_token = data["data"]["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


def create_track(headers: dict) -> str:
    title = unique_text("test_track")

    response = client.post(
        "/tracks/",
        headers=headers,
        json={
            "title": title,
            "description": "test description",
            "file_url": "test.mp3",
        },
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["success"] is True

    return data["data"]["track_id"]


def create_playlist(headers: dict) -> str:
    name = unique_text("test_playlist")

    response = client.post(
        "/playlists/",
        headers=headers,
        json={
            "name": name,
            "is_public": True,
        },
    )
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["success"] is True

    return data["data"]["playlist_id"]


def test_create_playlist():
    headers = login_and_get_headers()

    response = client.post(
        "/playlists/",
        headers=headers,
        json={
            "name": unique_text("create_playlist"),
            "is_public": False,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["success"] is True
    assert "playlist_id" in data["data"]
    assert data["data"]["name"].startswith("create_playlist")
    assert data["data"]["is_public"] is False


def test_get_playlist():
    headers = login_and_get_headers()
    playlist_id = create_playlist(headers)

    response = client.get(f"/playlists/{playlist_id}")

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["success"] is True
    assert data["data"]["playlist_id"] == playlist_id
    assert "name" in data["data"]
    assert "tracks" in data["data"]


def test_update_playlist():
    headers = login_and_get_headers()
    playlist_id = create_playlist(headers)

    response = client.patch(
        f"/playlists/{playlist_id}",
        headers=headers,
        json={
            "name": "updated_playlist_name",
            "description": "updated description",
            "is_public": False,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["success"] is True
    assert data["data"]["playlist_id"] == playlist_id
    assert data["data"]["name"] == "updated_playlist_name"
    assert data["data"]["description"] == "updated description"
    assert data["data"]["is_public"] is False


def test_search_tracks():
    headers = login_and_get_headers()
    unique_title = unique_text("searchable_track")

    create_response = client.post(
        "/tracks/",
        headers=headers,
        json={
            "title": unique_title,
            "description": "search test",
            "file_url": "test.mp3",
        },
    )
    assert create_response.status_code == 200, create_response.text

    response = client.get(f"/search/tracks?keyword={unique_title}")

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["success"] is True
    assert isinstance(data["data"]["tracks"], list)
    assert len(data["data"]["tracks"]) >= 1
    assert any(track["title"] == unique_title for track in data["data"]["tracks"])


def test_add_track_to_playlist():
    headers = login_and_get_headers()
    playlist_id = create_playlist(headers)
    track_id = create_track(headers)

    response = client.post(
        f"/playlists/{playlist_id}/tracks",
        headers=headers,
        json={"track_id": track_id},
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["success"] is True
    assert data["message"] == "Track added to playlist successfully."


def test_remove_track_from_playlist():
    headers = login_and_get_headers()
    playlist_id = create_playlist(headers)
    track_id = create_track(headers)

    add_response = client.post(
        f"/playlists/{playlist_id}/tracks",
        headers=headers,
        json={"track_id": track_id},
    )
    assert add_response.status_code == 200, add_response.text

    remove_response = client.delete(
        f"/playlists/{playlist_id}/tracks/{track_id}",
        headers=headers,
    )

    assert remove_response.status_code == 200, remove_response.text
    data = remove_response.json()

    assert data["success"] is True
    assert data["message"] == "Track removed from playlist successfully."


def test_delete_playlist():
    headers = login_and_get_headers()
    playlist_id = create_playlist(headers)

    delete_response = client.delete(
        f"/playlists/{playlist_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200, delete_response.text
    delete_data = delete_response.json()

    assert delete_data["success"] is True
    assert delete_data["message"] == "Playlist deleted successfully."

    get_response = client.get(f"/playlists/{playlist_id}")
    assert get_response.status_code == 404, get_response.text
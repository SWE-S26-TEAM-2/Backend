"""
HTTP-level tests for OAuth endpoints.

Covers POST /auth/google and POST /auth/facebook at the FastAPI
routing and validation layer using TestClient + monkeypatch.
Service internals (Google/Facebook SDK calls) are mocked so no
real network request is made.

Schema field names (confirmed from app/schemas/auth_schema.py):
  Google:   { "google_token":   "<id_token>" }
  Facebook: { "facebook_token": "<access_token>" }
"""

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.database.database import get_db
from app.services.auth_service import AuthService

client = TestClient(app)

_USER = {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "socialuser",
    "display_name": "Social User",
    "account_type": "listener",
    "is_premium": False,
    "billing_cycle": None,
}

_SOCIAL_SUCCESS = {
    "success": True,
    "data": {
        "access_token": "tok_access",
        "refresh_token": "tok_refresh",
        "token_type": "bearer",
        "expires_in": 900,
        "is_new_user": False,
        "user": _USER,
    },
}

_SOCIAL_NEW_USER = {
    "success": True,
    "data": {
        "access_token": "tok_access",
        "refresh_token": "tok_refresh",
        "token_type": "bearer",
        "expires_in": 900,
        "is_new_user": True,
        "user": _USER,
    },
}


class DummyDB:
    pass


def override_get_db():
    yield DummyDB()


def setup_module(module):
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(module):
    app.dependency_overrides.clear()


# ── POST /auth/google ───────────────────────────────────────────────────────────


def test_google_login_invalid_token_returns_401(monkeypatch):
    monkeypatch.setattr(
        AuthService,
        "google_login",
        lambda db, req: (_ for _ in ()).throw(
            HTTPException(status_code=401, detail="invalid")
        ),
    )
    response = client.post("/auth/google", json={"google_token": "bad"})
    assert response.status_code == 401


def test_google_login_missing_token_returns_422():
    response = client.post("/auth/google", json={})
    assert response.status_code == 422
    locs = [tuple(err["loc"]) for err in response.json()["detail"]]
    assert ("body", "google_token") in locs


def test_google_login_existing_user_returns_200(monkeypatch):
    monkeypatch.setattr(
        AuthService, "google_login", lambda db, req: _SOCIAL_SUCCESS
    )
    response = client.post("/auth/google", json={"google_token": "valid_tok"})
    assert response.status_code == 200
    assert response.json()["data"]["is_new_user"] is False


def test_google_login_new_user_returns_is_new_true(monkeypatch):
    monkeypatch.setattr(
        AuthService, "google_login", lambda db, req: _SOCIAL_NEW_USER
    )
    response = client.post("/auth/google", json={"google_token": "valid_tok"})
    assert response.status_code == 200
    assert response.json()["data"]["is_new_user"] is True
    assert "access_token" in response.json()["data"]


def test_google_login_returns_both_tokens(monkeypatch):
    monkeypatch.setattr(
        AuthService, "google_login", lambda db, req: _SOCIAL_SUCCESS
    )
    response = client.post("/auth/google", json={"google_token": "valid_tok"})
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


# ── POST /auth/facebook ─────────────────────────────────────────────────────────


def test_facebook_login_invalid_token_returns_401(monkeypatch):
    monkeypatch.setattr(
        AuthService,
        "facebook_login",
        lambda db, req: (_ for _ in ()).throw(
            HTTPException(status_code=401, detail="invalid")
        ),
    )
    response = client.post("/auth/facebook", json={"facebook_token": "bad"})
    assert response.status_code == 401


def test_facebook_login_missing_token_returns_422():
    response = client.post("/auth/facebook", json={})
    assert response.status_code == 422
    locs = [tuple(err["loc"]) for err in response.json()["detail"]]
    assert ("body", "facebook_token") in locs


def test_facebook_login_existing_user_returns_200(monkeypatch):
    monkeypatch.setattr(
        AuthService, "facebook_login", lambda db, req: _SOCIAL_SUCCESS
    )
    response = client.post(
        "/auth/facebook", json={"facebook_token": "valid_tok"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_new_user"] is False


def test_facebook_login_new_user_returns_is_new_true(monkeypatch):
    monkeypatch.setattr(
        AuthService, "facebook_login", lambda db, req: _SOCIAL_NEW_USER
    )
    response = client.post(
        "/auth/facebook", json={"facebook_token": "valid_tok"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_new_user"] is True
    assert "access_token" in response.json()["data"]


def test_facebook_login_returns_both_tokens(monkeypatch):
    monkeypatch.setattr(
        AuthService, "facebook_login", lambda db, req: _SOCIAL_SUCCESS
    )
    response = client.post(
        "/auth/facebook", json={"facebook_token": "valid_tok"}
    )
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

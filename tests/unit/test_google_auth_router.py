"""
HTTP-level tests for POST /auth/google (Google OAuth2 login / auto-registration).

These tests exercise the FastAPI routing + request validation layer using
TestClient so regressions in schema validation, HTTP status codes, and
response shape are caught before they reach production.

Facebook OAuth is intentionally NOT tested here — it is a placeholder
endpoint that has been explicitly excluded from scope.

Scenarios covered
-----------------
1. Missing ``google_token`` field in body        → 422 (validation error)
2. Empty string ``google_token``                 → 400 (Bad Request)
3. Invalid / expired Google token               → 401 (Unauthorized)
4. Google OAuth service unreachable             → 503 (Service Unavailable)
5. Suspended account tries to login             → 403 (Forbidden)
6. Existing user logs in successfully           → 200, is_new_user=False
7. New user is auto-registered                  → 200, is_new_user=True
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from app.main import app
from app.services.auth_service import AuthService

# ---------------------------------------------------------------------------
# Shared TestClient
# ---------------------------------------------------------------------------

client = TestClient(app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# Helper: a minimal valid google_login success response from AuthService
# ---------------------------------------------------------------------------


def _make_success_response(*, is_new_user: bool = False) -> dict:
    uid = str(uuid.uuid4())
    return {
        "success": True,
        "data": {
            "access_token": "fake-access-token",
            "refresh_token": "fake-refresh-token",
            "token_type": "bearer",
            "expires_in": 900,
            "is_new_user": is_new_user,
            "user": {
                "user_id": uid,
                "username": "testuser",
                "display_name": "Test User",
                "account_type": "listener",
                "is_premium": False,
                "billing_cycle": None,
            },
        },
    }


# ---------------------------------------------------------------------------
# 1. Missing google_token field → 422 Unprocessable Entity
# ---------------------------------------------------------------------------


def test_google_login_missing_field_returns_422():
    """POST /auth/google with an empty body must return 422 (schema validation)."""
    response = client.post("/auth/google", json={})
    assert response.status_code == 422
    detail = response.json()["detail"]
    # FastAPI validation error points to the missing field
    locs = [err["loc"] for err in detail]
    assert any("google_token" in loc for loc in locs), (
        f"Expected 'google_token' in validation error locs, got: {locs}"
    )


# ---------------------------------------------------------------------------
# 2. Empty google_token string → 400 Bad Request
# ---------------------------------------------------------------------------


def test_google_login_empty_token_returns_400(monkeypatch):
    """POST /auth/google with google_token='' must return 400."""
    monkeypatch.setattr(
        AuthService,
        "google_login",
        lambda db, req: (_ for _ in ()).throw(
            HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing or empty google_token.",
            )
        ),
    )
    response = client.post("/auth/google", json={"google_token": ""})
    assert response.status_code == 400
    assert "google_token" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 3. Invalid / expired Google token → 401 Unauthorized
# ---------------------------------------------------------------------------


def test_google_login_invalid_token_returns_401(monkeypatch):
    """POST /auth/google with a bad token must return 401."""
    monkeypatch.setattr(
        AuthService,
        "google_login",
        lambda db, req: (_ for _ in ()).throw(
            HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token invalid or expired.",
            )
        ),
    )
    response = client.post("/auth/google", json={"google_token": "not-a-real-token"})
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower() or \
           "expired" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. Google OAuth service unreachable → 503 Service Unavailable
# ---------------------------------------------------------------------------


def test_google_login_service_unreachable_returns_503(monkeypatch):
    """POST /auth/google when Google is down must return 503."""
    monkeypatch.setattr(
        AuthService,
        "google_login",
        lambda db, req: (_ for _ in ()).throw(
            HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth service unavailable.",
            )
        ),
    )
    response = client.post("/auth/google", json={"google_token": "any-token"})
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# 5. Suspended account → 403 Forbidden
# ---------------------------------------------------------------------------


def test_google_login_suspended_account_returns_403(monkeypatch):
    """POST /auth/google for a suspended user must return 403."""
    monkeypatch.setattr(
        AuthService,
        "google_login",
        lambda db, req: (_ for _ in ()).throw(
            HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account suspended.",
            )
        ),
    )
    response = client.post("/auth/google", json={"google_token": "valid-token"})
    assert response.status_code == 403
    assert "suspended" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6. Existing user logs in successfully → 200, is_new_user=False
# ---------------------------------------------------------------------------


def test_google_login_existing_user_returns_200(monkeypatch):
    """POST /auth/google for an existing user must return 200 with is_new_user=False."""
    mock_response = _make_success_response(is_new_user=False)
    monkeypatch.setattr(
        AuthService,
        "google_login",
        lambda db, req: mock_response,
    )
    response = client.post("/auth/google", json={"google_token": "valid-existing-token"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["is_new_user"] is False
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data["user"]


# ---------------------------------------------------------------------------
# 7. New user is auto-registered → 200, is_new_user=True
# ---------------------------------------------------------------------------


def test_google_login_new_user_returns_200_with_is_new_true(monkeypatch):
    """POST /auth/google for a brand-new Google account must return 200 with is_new_user=True."""
    mock_response = _make_success_response(is_new_user=True)
    monkeypatch.setattr(
        AuthService,
        "google_login",
        lambda db, req: mock_response,
    )
    response = client.post("/auth/google", json={"google_token": "valid-new-user-token"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["is_new_user"] is True
    assert "access_token" in data
    assert data["user"]["account_type"] == "listener"


# ---------------------------------------------------------------------------
# 8. Response shape validation — all required fields present
# ---------------------------------------------------------------------------


def test_google_login_response_contains_all_required_fields(monkeypatch):
    """Verify the full response envelope matches the SocialLoginResponse schema."""
    mock_response = _make_success_response(is_new_user=False)
    monkeypatch.setattr(
        AuthService,
        "google_login",
        lambda db, req: mock_response,
    )
    response = client.post("/auth/google", json={"google_token": "valid-token"})
    assert response.status_code == 200
    data = response.json()["data"]

    required_top = {"access_token", "refresh_token", "token_type", "expires_in",
                    "is_new_user", "user"}
    assert required_top.issubset(data.keys()), (
        f"Missing top-level keys: {required_top - data.keys()}"
    )

    required_user = {"user_id", "username", "display_name", "account_type",
                     "is_premium", "billing_cycle"}
    assert required_user.issubset(data["user"].keys()), (
        f"Missing user keys: {required_user - data['user'].keys()}"
    )

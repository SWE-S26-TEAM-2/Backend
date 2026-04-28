"""HTTP-level tests for /auth/* endpoints.

Strategy: every test monkeypatches the relevant ``AuthService`` static
method so we can assert the *router* surface (status code, body shape,
schema validation, dependency wiring) without standing up the real
repositories or token tables.

Strict failure-mode contracts under test:
  - login wrong password   -> 401 (service raises 401)
  - login unverified user  -> 403 (service raises 403)
  - register duplicate     -> 409
  - reset weak password    -> 422 (schema validator)
  - missing required field -> 422 (Pydantic)
  - rate-limited paths     -> 429 when service raises 429
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from app.services.auth_service import AuthService


# ── Register ─────────────────────────────────────────────


def test_register_success(client, monkeypatch):
    user_id = uuid.uuid4()

    def fake_register(db, request):
        return {
            "success": True,
            "message": "Registration successful.",
            "data": {
                "user_id": str(user_id),
                "email": request.email,
                "username": request.username.lower(),
                "display_name": request.display_name,
                "is_verified": False,
            },
        }

    monkeypatch.setattr(AuthService, "register_user", fake_register)

    response = client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "Strong1Password",
            "display_name": "New User",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "new@example.com"
    assert body["data"]["username"] == "newuser"


def test_register_duplicate_returns_409(client, monkeypatch):
    def fake_register(db, request):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    monkeypatch.setattr(AuthService, "register_user", fake_register)

    response = client.post(
        "/auth/register",
        json={
            "email": "dup@example.com",
            "username": "dupuser",
            "password": "Strong1Password",
            "display_name": "Dup",
        },
    )

    assert response.status_code == 409
    assert "already" in response.json()["detail"].lower()


def test_register_invalid_email_returns_422(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "username": "u1",
            "password": "Strong1Password",
            "display_name": "X",
        },
    )

    assert response.status_code == 422


def test_register_short_username_returns_422(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "x@example.com",
            "username": "ab",
            "password": "Strong1Password",
            "display_name": "X",
        },
    )

    assert response.status_code == 422


def test_register_short_password_returns_422(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "x@example.com",
            "username": "validuser",
            "password": "short",
            "display_name": "X",
        },
    )

    assert response.status_code == 422


def test_register_missing_required_field_returns_422(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "x@example.com",
            "username": "validuser",
            "password": "Strong1Password",
        },
    )

    assert response.status_code == 422


# ── Login ────────────────────────────────────────────────


def _login_success_payload(user_id: uuid.UUID) -> dict:
    return {
        "success": True,
        "data": {
            "access_token": "access-token-xyz",
            "refresh_token": "refresh-token-xyz",
            "token_type": "bearer",
            "expires_in": 900,
            "user": {
                "user_id": str(user_id),
                "username": "testuser",
                "display_name": "Test User",
                "account_type": "listener",
                "is_premium": False,
            },
        },
    }


def test_login_success(client, monkeypatch):
    user_id = uuid.uuid4()
    monkeypatch.setattr(
        AuthService,
        "login_user",
        lambda db, data: _login_success_payload(user_id),
    )

    response = client.post(
        "/auth/login",
        json={"identifier": "user@example.com", "password": "Strong1Password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
    assert body["data"]["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client, monkeypatch):
    def fake_login(db, data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    monkeypatch.setattr(AuthService, "login_user", fake_login)

    response = client.post(
        "/auth/login",
        json={"identifier": "user@example.com", "password": "Wrong1Password"},
    )

    assert response.status_code == 401


def test_login_unverified_returns_403(client, monkeypatch):
    """Service contract: unverified accounts return 403, not 401."""
    def fake_login(db, data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified",
        )

    monkeypatch.setattr(AuthService, "login_user", fake_login)

    response = client.post(
        "/auth/login",
        json={"identifier": "u@example.com", "password": "Strong1Password"},
    )

    # Service raises 403 for unverified accounts (see auth_service.login_user).
    assert response.status_code == 403


def test_login_missing_password_returns_422(client):
    response = client.post(
        "/auth/login",
        json={"identifier": "u@example.com"},
    )

    assert response.status_code == 422


# ── Refresh ──────────────────────────────────────────────


def test_refresh_success_returns_new_pair(client, monkeypatch):
    monkeypatch.setattr(
        AuthService,
        "refresh_access_token",
        lambda db, data: {
            "success": True,
            "data": {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "token_type": "bearer",
                "expires_in": 900,
            },
        },
    )

    response = client.post(
        "/auth/refresh", json={"refresh_token": "old-refresh-token"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["access_token"] == "new-access"
    assert body["data"]["refresh_token"] == "new-refresh"


def test_refresh_revoked_returns_401(client, monkeypatch):
    def fake_refresh(db, data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or already used.",
        )

    monkeypatch.setattr(AuthService, "refresh_access_token", fake_refresh)

    response = client.post(
        "/auth/refresh", json={"refresh_token": "revoked-token"}
    )

    assert response.status_code == 401


def test_refresh_missing_field_returns_422(client):
    response = client.post("/auth/refresh", json={})
    assert response.status_code == 422


# ── Logout ───────────────────────────────────────────────


def test_logout_success_then_refresh_revoked(client, override_auth, monkeypatch):
    """Logout returns 200 and subsequent refresh with the same token 401."""
    override_auth()

    def fake_logout(db, data, current_user):
        return {"success": True, "message": "Logged out successfully."}

    monkeypatch.setattr(AuthService, "logout", fake_logout)

    logout_resp = client.post(
        "/auth/logout", json={"refresh_token": "valid-refresh"}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True

    def fake_refresh_revoked(db, data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or already used.",
        )

    monkeypatch.setattr(AuthService, "refresh_access_token", fake_refresh_revoked)

    refresh_resp = client.post(
        "/auth/refresh", json={"refresh_token": "valid-refresh"}
    )
    assert refresh_resp.status_code == 401


def test_logout_without_auth_returns_401(client):
    response = client.post(
        "/auth/logout", json={"refresh_token": "anything"}
    )
    assert response.status_code == 401


# ── Forgot / Reset password ──────────────────────────────


def test_forgot_password_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        AuthService,
        "forgot_password",
        lambda db, data: {
            "success": True,
            "message": "If an account exists, a reset link has been sent.",
        },
    )

    response = client.post(
        "/auth/forgot-password", json={"email": "u@example.com"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_forgot_password_rate_limit_returns_429(client, monkeypatch):
    """Service contract: 3 requests per hour (PasswordResetRepository.count_recent).

    We simulate the 4th attempt by raising 429 from the service.
    """
    call_count = {"n": 0}

    def fake_forgot(db, data):
        call_count["n"] += 1
        if call_count["n"] >= 4:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Max 3 reset requests per hour.",
            )
        return {"success": True, "message": "ok"}

    monkeypatch.setattr(AuthService, "forgot_password", fake_forgot)

    for _ in range(3):
        ok = client.post(
            "/auth/forgot-password", json={"email": "x@example.com"}
        )
        assert ok.status_code == 200

    response = client.post(
        "/auth/forgot-password", json={"email": "x@example.com"}
    )
    assert response.status_code == 429
    assert call_count["n"] == 4


def test_forgot_password_invalid_email_returns_422(client):
    response = client.post(
        "/auth/forgot-password", json={"email": "not-an-email"}
    )
    assert response.status_code == 422


def test_reset_password_weak_password_returns_422(client):
    """ResetPasswordRequest enforces uppercase + digit at the schema layer."""
    response = client.post(
        "/auth/reset-password",
        json={"token": "any-token", "new_password": "alllowercase"},
    )
    assert response.status_code == 422


def test_reset_password_success(client, monkeypatch):
    monkeypatch.setattr(
        AuthService,
        "reset_password",
        lambda db, data: {
            "success": True,
            "message": "Password updated successfully.",
        },
    )

    response = client.post(
        "/auth/reset-password",
        json={"token": "valid-token", "new_password": "Strong1NewPassword"},
    )

    assert response.status_code == 200


# ── Verify-email / Resend-verification ───────────────────


def test_verify_email_success(client, monkeypatch):
    monkeypatch.setattr(
        AuthService,
        "verify_email",
        lambda db, data: {"success": True, "message": "Account verified."},
    )

    response = client.post("/auth/verify-email", json={"token": "abc"})
    assert response.status_code == 200


def test_resend_verification_rate_limited_returns_429(client, monkeypatch):
    def fake_resend(db, data):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded.",
        )

    monkeypatch.setattr(AuthService, "resend_verification", fake_resend)

    response = client.post(
        "/auth/resend-verification", json={"email": "u@example.com"}
    )
    assert response.status_code == 429

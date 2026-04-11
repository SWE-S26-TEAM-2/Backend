# Unit Testing Guide for the Backend Team

This guide explains how to write and run unit tests for our SoundCloud Clone API.

## Quick Start

```bash
# Install pytest (one time)
pip install pytest

# Run all tests
pytest

# Run tests for one file
pytest tests/unit/test_auth_service.py

# Run a single test by name
pytest tests/unit/test_auth_service.py -k "test_register_success"

# Run with verbose output (see each test name)
pytest -v
```

## How Unit Tests Work

Unit tests check that each **service function** works correctly **without needing a real database**. We use `MagicMock` to fake the database — this makes tests fast and reliable.

### File Structure

```
tests/
  unit/
    conftest.py              # Shared helpers and fixtures (fake users, mock DB)
    test_auth_service.py     # Tests for AuthService
    test_user_service.py     # Tests for UserService
    test_follower_service.py # Tests for FollowerService
    ...
```

### Naming Rules

- Test files: `test_<service_name>.py`
- Test functions: `test_<what_you_are_testing>`
- Example: `test_register_duplicate_email` in `test_auth_service.py`

## Step-by-Step: Writing Your First Test

### 1. Create the conftest.py file (shared fixtures)

Create `tests/unit/conftest.py`:

```python
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


def make_fake_user(**overrides):
    """Build a MagicMock that looks like a User ORM object."""
    defaults = {
        "user_id": uuid.uuid4(),
        "email": "test@example.com",
        "password_hash": "$2b$12$hashedpasswordplaceholder",
        "display_name": "TestUser",
        "account_type": "listener",
        "is_verified": True,
        "is_suspended": False,
        "bio": None,
        "location": None,
        "is_premium": False,
        "is_private": False,
        "profile_picture": None,
        "cover_photo": None,
        "follower_count": 0,
        "following_count": 0,
        "track_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    defaults.update(overrides)
    user = MagicMock()
    for key, value in defaults.items():
        setattr(user, key, value)
    return user


@pytest.fixture
def mock_db():
    """Return a MagicMock pretending to be a SQLAlchemy Session."""
    return MagicMock()


@pytest.fixture
def verified_user():
    """Return a verified, non-suspended user."""
    return make_fake_user()


@pytest.fixture
def unverified_user():
    """Return a user whose email is NOT yet verified."""
    return make_fake_user(is_verified=False)


@pytest.fixture
def suspended_user():
    """Return a verified but suspended user."""
    return make_fake_user(is_suspended=True)
```

### 2. Write a test file

Create `tests/unit/test_auth_service.py`:

```python
"""Tests for AuthService."""

from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException

from app.services.auth_service import AuthService


class TestRegisterUser:
    """Tests for AuthService.register_user()"""

    @patch("app.services.auth_service.TokenRepository")
    @patch("app.services.auth_service.UserRepository")
    def test_register_success(self, mock_user_repo, mock_token_repo, mock_db):
        """New user registers successfully."""
        # Setup: no existing user with this email
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = None

        # The request data
        data = MagicMock()
        data.email = "new@example.com"
        data.password = "StrongPass1!"
        data.display_name = "New User"
        data.account_type = "listener"

        # Call the service
        result = AuthService.register_user(mock_db, data)

        # Check the result
        assert result["success"] is True
        assert "Registration successful" in result["message"]
        mock_user_repo.create.assert_called_once()

    @patch("app.services.auth_service.UserRepository")
    def test_register_duplicate_email(self, mock_user_repo, mock_db, verified_user):
        """Registering with an existing email returns 409."""
        # Setup: email already exists
        mock_user_repo.get_by_email.return_value = verified_user

        data = MagicMock()
        data.email = "test@example.com"

        # Should raise 409
        with pytest.raises(HTTPException) as exc_info:
            AuthService.register_user(mock_db, data)
        assert exc_info.value.status_code == 409


class TestLoginUser:
    """Tests for AuthService.login_user()"""

    @patch("app.services.auth_service.RefreshTokenRepository")
    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_login_success(self, mock_user_repo, mock_verify, mock_refresh_repo,
                           mock_db, verified_user):
        """Verified user logs in successfully."""
        mock_user_repo.get_by_email.return_value = verified_user

        data = MagicMock()
        data.email = "test@example.com"
        data.password = "StrongPass1!"

        result = AuthService.login_user(mock_db, data)
        assert result["success"] is True
        assert "access_token" in result["data"]
        assert "refresh_token" in result["data"]

    @patch("app.services.auth_service.verify_password", return_value=False)
    @patch("app.services.auth_service.UserRepository")
    def test_login_wrong_password(self, mock_user_repo, mock_verify,
                                  mock_db, verified_user):
        """Wrong password returns 401."""
        mock_user_repo.get_by_email.return_value = verified_user

        data = MagicMock()
        data.email = "test@example.com"
        data.password = "WrongPass1!"

        with pytest.raises(HTTPException) as exc_info:
            AuthService.login_user(mock_db, data)
        assert exc_info.value.status_code == 401

    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_login_unverified(self, mock_user_repo, mock_verify,
                              mock_db, unverified_user):
        """Unverified user gets 403."""
        mock_user_repo.get_by_email.return_value = unverified_user

        data = MagicMock()
        data.email = "test@example.com"
        data.password = "StrongPass1!"

        with pytest.raises(HTTPException) as exc_info:
            AuthService.login_user(mock_db, data)
        assert exc_info.value.status_code == 403

    @patch("app.services.auth_service.verify_password", return_value=True)
    @patch("app.services.auth_service.UserRepository")
    def test_login_suspended(self, mock_user_repo, mock_verify,
                             mock_db, suspended_user):
        """Suspended user gets 403."""
        mock_user_repo.get_by_email.return_value = suspended_user

        data = MagicMock()
        data.email = "test@example.com"
        data.password = "StrongPass1!"

        with pytest.raises(HTTPException) as exc_info:
            AuthService.login_user(mock_db, data)
        assert exc_info.value.status_code == 403

    @patch("app.services.auth_service.UserRepository")
    def test_login_nonexistent_email(self, mock_user_repo, mock_db):
        """Nonexistent email returns 401."""
        mock_user_repo.get_by_email.return_value = None

        data = MagicMock()
        data.email = "noone@example.com"
        data.password = "StrongPass1!"

        with pytest.raises(HTTPException) as exc_info:
            AuthService.login_user(mock_db, data)
        assert exc_info.value.status_code == 401
```

## The Pattern: How Every Test Works

Every test follows the same 3 steps:

```
1. SETUP    — Fake the database responses (mock_repo.get_by_email.return_value = ...)
2. CALL     — Call the service method (AuthService.login_user(mock_db, data))
3. CHECK    — Assert the result or exception (assert result["success"] is True)
```

### Testing Success Cases

```python
result = AuthService.some_method(mock_db, data)
assert result["success"] is True
assert result["data"]["field"] == expected_value
```

### Testing Error Cases

```python
with pytest.raises(HTTPException) as exc_info:
    AuthService.some_method(mock_db, data)
assert exc_info.value.status_code == 404
```

## How to Mock the Right Things

When a service calls a repository, you mock the repository:

```python
@patch("app.services.auth_service.UserRepository")
def test_something(self, mock_user_repo, mock_db):
    # Control what the repo returns
    mock_user_repo.get_by_email.return_value = some_fake_user
```

The `@patch` decorator replaces the real repository with a fake one during the test. The string inside `@patch()` must match the **import path in the service file**.

## Checklist: What to Test for Each Service

For each service method, write tests for:

- [ ] **Happy path** — the normal success case
- [ ] **Not found** — entity doesn't exist (expect 404)
- [ ] **Unauthorized** — user shouldn't have access (expect 401/403)
- [ ] **Duplicate/conflict** — already exists (expect 409)
- [ ] **Bad input** — missing or invalid data (expect 400/422)

## Running Tests in CI

Tests run automatically on every push/PR via GitHub Actions. The CI runs:
```
pytest || [ $? -eq 5 ]
```
This means pytest runs, and exit code 5 (no tests collected) is treated as a pass.

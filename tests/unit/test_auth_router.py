from fastapi.testclient import TestClient

from app.database.database import get_db
from app.main import app
from app.services.auth_service import AuthService

client = TestClient(app)


class DummyDB:
    pass


def override_get_db():
    yield DummyDB()


def setup_module(module):
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(module):
    app.dependency_overrides.clear()


def test_bootstrap_admin_success(monkeypatch):
    monkeypatch.setattr(
        AuthService,
        "bootstrap_admin",
        lambda db, request, bootstrap_secret: {
            "success": True,
            "message": "Initial admin account created successfully.",
            "data": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": request.email,
                "username": request.username,
                "display_name": request.display_name,
                "role": "admin",
                "is_verified": True,
            },
        },
    )

    response = client.post(
        "/auth/bootstrap-admin",
        headers={"X-Admin-Bootstrap-Secret": "bootstrap-secret"},
        json={
            "email": "admin@example.com",
            "username": "adminuser",
            "password": "StrongPass1",
            "display_name": "Admin User",
            "account_type": "listener",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "admin"

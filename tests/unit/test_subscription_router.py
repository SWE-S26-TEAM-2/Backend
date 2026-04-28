from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.services.subscription_service import SubscriptionService
from tests.unit.conftest import make_fake_user

client = TestClient(app)


class DummyDB:
    pass


def override_get_db():
    yield DummyDB()


def setup_module(module):
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(module):
    app.dependency_overrides.clear()


# ── GET /subscriptions/me ───────────────────────────────────────────────────────


def test_get_subscription_no_auth():
    response = client.get("/subscriptions/me")
    assert response.status_code == 401


def test_get_subscription_free_user(monkeypatch):
    fake_user = make_fake_user(is_premium=False, track_count=2)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "get_subscription",
        lambda user: {
            "success": True,
            "data": {"plan": "Free", "tracks_uploaded": 2, "limit": 3},
        },
    )

    response = client.get("/subscriptions/me")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["plan"] == "Free"
    assert body["data"]["limit"] == 3

    app.dependency_overrides.pop(get_current_user, None)


def test_get_subscription_premium_user(monkeypatch):
    fake_user = make_fake_user(is_premium=True, track_count=7)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "get_subscription",
        lambda user: {
            "success": True,
            "data": {"plan": "Premium", "tracks_uploaded": 7, "limit": None},
        },
    )

    response = client.get("/subscriptions/me")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["plan"] == "Premium"
    assert body["data"]["limit"] is None

    app.dependency_overrides.pop(get_current_user, None)


# ── POST /subscriptions/upgrade ─────────────────────────────────────────────────


def test_upgrade_no_auth():
    response = client.post(
        "/subscriptions/upgrade",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 401


def test_upgrade_success(monkeypatch):
    fake_user = make_fake_user(is_premium=False)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "upgrade",
        lambda db, user, token, plan: {
            "success": True,
            "message": "Welcome to Premium! Unlimited uploads unlocked.",
        },
    )

    response = client.post(
        "/subscriptions/upgrade",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "Premium" in body["message"]

    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_card_declined(monkeypatch):
    fake_user = make_fake_user(is_premium=False)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "upgrade",
        lambda db, user, token, plan: (_ for _ in ()).throw(
            HTTPException(status_code=402, detail="Card declined")
        ),
    )

    response = client.post(
        "/subscriptions/upgrade",
        json={"payment_token": "tok_chargeDeclined", "plan": "Premium"},
    )
    assert response.status_code == 402

    app.dependency_overrides.pop(get_current_user, None)

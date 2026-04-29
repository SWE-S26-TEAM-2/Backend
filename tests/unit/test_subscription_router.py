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
            "data": {
                "plan": "Free",
                "tracks_uploaded": 2,
                "limit": 3,
                "billing_cycle": None,
            },
        },
    )

    response = client.get("/subscriptions/me")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["plan"] == "Free"
    assert body["data"]["limit"] == 3
    assert body["data"]["billing_cycle"] is None

    app.dependency_overrides.pop(get_current_user, None)


def test_get_subscription_premium_monthly(monkeypatch):
    fake_user = make_fake_user(is_premium=True, track_count=7, billing_cycle="monthly")
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "get_subscription",
        lambda user: {
            "success": True,
            "data": {
                "plan": "Premium",
                "tracks_uploaded": 7,
                "limit": None,
                "billing_cycle": "monthly",
            },
        },
    )

    response = client.get("/subscriptions/me")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["plan"] == "Premium"
    assert body["data"]["billing_cycle"] == "monthly"

    app.dependency_overrides.pop(get_current_user, None)


def test_get_subscription_premium_yearly(monkeypatch):
    fake_user = make_fake_user(is_premium=True, track_count=4, billing_cycle="yearly")
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "get_subscription",
        lambda user: {
            "success": True,
            "data": {
                "plan": "Premium",
                "tracks_uploaded": 4,
                "limit": None,
                "billing_cycle": "yearly",
            },
        },
    )

    response = client.get("/subscriptions/me")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["billing_cycle"] == "yearly"

    app.dependency_overrides.pop(get_current_user, None)


# ── POST /subscriptions/upgrade/monthly ────────────────────────────────────────


def test_upgrade_monthly_no_auth():
    response = client.post(
        "/subscriptions/upgrade/monthly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 401


def test_upgrade_monthly_success(monkeypatch):
    fake_user = make_fake_user(is_premium=False)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "upgrade",
        lambda db, user, token, plan, cycle: {
            "success": True,
            "message": "Welcome to Premium! Unlimited uploads unlocked.",
        },
    )

    response = client.post(
        "/subscriptions/upgrade/monthly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "Premium" in body["message"]

    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_monthly_card_declined(monkeypatch):
    fake_user = make_fake_user(is_premium=False)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "upgrade",
        lambda db, user, token, plan, cycle: (_ for _ in ()).throw(
            HTTPException(status_code=402, detail="Card declined")
        ),
    )

    response = client.post(
        "/subscriptions/upgrade/monthly",
        json={"payment_token": "tok_chargeDeclined", "plan": "Premium"},
    )
    assert response.status_code == 402

    app.dependency_overrides.pop(get_current_user, None)


# ── POST /subscriptions/upgrade/yearly ─────────────────────────────────────────


def test_upgrade_yearly_no_auth():
    response = client.post(
        "/subscriptions/upgrade/yearly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 401


def test_upgrade_yearly_success(monkeypatch):
    fake_user = make_fake_user(is_premium=False)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "upgrade",
        lambda db, user, token, plan, cycle: {
            "success": True,
            "message": "Welcome to Premium! Unlimited uploads unlocked.",
        },
    )

    response = client.post(
        "/subscriptions/upgrade/yearly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_yearly_card_declined(monkeypatch):
    fake_user = make_fake_user(is_premium=False)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    monkeypatch.setattr(
        SubscriptionService,
        "upgrade",
        lambda db, user, token, plan, cycle: (_ for _ in ()).throw(
            HTTPException(status_code=402, detail="Card declined")
        ),
    )

    response = client.post(
        "/subscriptions/upgrade/yearly",
        json={"payment_token": "tok_chargeDeclined", "plan": "Premium"},
    )
    assert response.status_code == 402

    app.dependency_overrides.pop(get_current_user, None)

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


_SUCCESS = {
    "success": True,
    "message": "Welcome to Premium! Unlimited uploads unlocked.",
}


# ── GET /subscriptions/me ───────────────────────────────────────────────────────


def test_get_subscription_no_auth():
    response = client.get("/subscriptions/me")
    assert response.status_code == 401


def test_get_subscription_free_user(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "get_subscription",
        lambda user: {
            "success": True,
            "data": {"plan": "Free", "tracks_uploaded": 1,
                     "limit": 3, "billing_cycle": None},
        },
    )
    response = client.get("/subscriptions/me")
    assert response.status_code == 200
    assert response.json()["data"]["plan"] == "Free"
    app.dependency_overrides.pop(get_current_user, None)


def test_get_subscription_standard_premium(monkeypatch):
    user = make_fake_user(
        is_premium=True, billing_cycle="monthly", subscription_tier="standard"
    )
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(
        SubscriptionService, "get_subscription",
        lambda u: {
            "success": True,
            "data": {"plan": "Premium", "tracks_uploaded": 5,
                     "limit": None, "billing_cycle": "monthly"},
        },
    )
    response = client.get("/subscriptions/me")
    assert response.status_code == 200
    assert response.json()["data"]["plan"] == "Premium"
    app.dependency_overrides.pop(get_current_user, None)


def test_get_subscription_pro(monkeypatch):
    user = make_fake_user(
        is_premium=True, billing_cycle="yearly", subscription_tier="pro"
    )
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(
        SubscriptionService, "get_subscription",
        lambda u: {
            "success": True,
            "data": {"plan": "Pro", "tracks_uploaded": 10,
                     "limit": None, "billing_cycle": "yearly"},
        },
    )
    response = client.get("/subscriptions/me")
    assert response.status_code == 200
    assert response.json()["data"]["plan"] == "Pro"
    app.dependency_overrides.pop(get_current_user, None)


# ── Standard — /upgrade/monthly ────────────────────────────────────────────────


def test_upgrade_monthly_no_auth():
    response = client.post(
        "/subscriptions/upgrade/monthly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 401


def test_upgrade_monthly_success(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: _SUCCESS,
    )
    response = client.post(
        "/subscriptions/upgrade/monthly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 200
    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_monthly_card_declined(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: (_ for _ in ()).throw(
            HTTPException(status_code=402, detail="Card declined")
        ),
    )
    response = client.post(
        "/subscriptions/upgrade/monthly",
        json={"payment_token": "tok_chargeDeclined", "plan": "Premium"},
    )
    assert response.status_code == 402
    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_monthly_already_subscribed_returns_409(monkeypatch):
    user = make_fake_user(
        is_premium=True, billing_cycle="monthly", subscription_tier="standard"
    )
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: (_ for _ in ()).throw(
            HTTPException(status_code=409, detail="Already subscribed.")
        ),
    )
    response = client.post(
        "/subscriptions/upgrade/monthly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 409
    app.dependency_overrides.pop(get_current_user, None)


# ── Standard — /upgrade/yearly ─────────────────────────────────────────────────


def test_upgrade_yearly_no_auth():
    response = client.post(
        "/subscriptions/upgrade/yearly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 401


def test_upgrade_yearly_success(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: _SUCCESS,
    )
    response = client.post(
        "/subscriptions/upgrade/yearly",
        json={"payment_token": "tok_visa", "plan": "Premium"},
    )
    assert response.status_code == 200
    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_yearly_card_declined(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: (_ for _ in ()).throw(
            HTTPException(status_code=402, detail="Card declined")
        ),
    )
    response = client.post(
        "/subscriptions/upgrade/yearly",
        json={"payment_token": "tok_chargeDeclined", "plan": "Premium"},
    )
    assert response.status_code == 402
    app.dependency_overrides.pop(get_current_user, None)


# ── Pro — /upgrade/pro/monthly ─────────────────────────────────────────────────


def test_upgrade_pro_monthly_no_auth():
    response = client.post(
        "/subscriptions/upgrade/pro/monthly",
        json={"payment_token": "tok_visa", "plan": "Pro"},
    )
    assert response.status_code == 401


def test_upgrade_pro_monthly_success(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: _SUCCESS,
    )
    response = client.post(
        "/subscriptions/upgrade/pro/monthly",
        json={"payment_token": "tok_visa", "plan": "Pro"},
    )
    assert response.status_code == 200
    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_pro_monthly_card_declined(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: (_ for _ in ()).throw(
            HTTPException(status_code=402, detail="Card declined")
        ),
    )
    response = client.post(
        "/subscriptions/upgrade/pro/monthly",
        json={"payment_token": "tok_chargeDeclined", "plan": "Pro"},
    )
    assert response.status_code == 402
    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_pro_monthly_already_subscribed_returns_409(monkeypatch):
    user = make_fake_user(
        is_premium=True, billing_cycle="monthly", subscription_tier="pro"
    )
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: (_ for _ in ()).throw(
            HTTPException(status_code=409, detail="Already subscribed.")
        ),
    )
    response = client.post(
        "/subscriptions/upgrade/pro/monthly",
        json={"payment_token": "tok_visa", "plan": "Pro"},
    )
    assert response.status_code == 409
    app.dependency_overrides.pop(get_current_user, None)


# ── Pro — /upgrade/pro/yearly ──────────────────────────────────────────────────


def test_upgrade_pro_yearly_no_auth():
    response = client.post(
        "/subscriptions/upgrade/pro/yearly",
        json={"payment_token": "tok_visa", "plan": "Pro"},
    )
    assert response.status_code == 401


def test_upgrade_pro_yearly_success(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: _SUCCESS,
    )
    response = client.post(
        "/subscriptions/upgrade/pro/yearly",
        json={"payment_token": "tok_visa", "plan": "Pro"},
    )
    assert response.status_code == 200
    app.dependency_overrides.pop(get_current_user, None)


def test_upgrade_pro_yearly_card_declined(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: make_fake_user()
    monkeypatch.setattr(
        SubscriptionService, "upgrade",
        lambda db, user, token, plan, cycle, tier: (_ for _ in ()).throw(
            HTTPException(status_code=402, detail="Card declined")
        ),
    )
    response = client.post(
        "/subscriptions/upgrade/pro/yearly",
        json={"payment_token": "tok_chargeDeclined", "plan": "Pro"},
    )
    assert response.status_code == 402
    app.dependency_overrides.pop(get_current_user, None)

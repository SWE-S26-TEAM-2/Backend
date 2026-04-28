import pytest
import stripe
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from app.services.subscription_service import SubscriptionService
from tests.unit.conftest import make_fake_user

# ── get_subscription ────────────────────────────────────────────────────────────


def test_get_subscription_free_user():
    user = make_fake_user(is_premium=False, track_count=2)
    result = SubscriptionService.get_subscription(user)
    assert result["success"] is True
    assert result["data"]["plan"] == "Free"
    assert result["data"]["tracks_uploaded"] == 2
    assert result["data"]["limit"] == 3


def test_get_subscription_premium_user():
    user = make_fake_user(is_premium=True, track_count=10)
    result = SubscriptionService.get_subscription(user)
    assert result["data"]["plan"] == "Premium"
    assert result["data"]["tracks_uploaded"] == 10
    assert result["data"]["limit"] is None


# ── upgrade ─────────────────────────────────────────────────────────────────────


def test_upgrade_invalid_plan_raises_400():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        SubscriptionService.upgrade(db, user, "tok_visa", "Free")
    assert exc_info.value.status_code == 400


def test_upgrade_already_premium_is_idempotent():
    user = make_fake_user(is_premium=True)
    db = MagicMock()
    with patch("app.services.subscription_service.stripe.Charge.create") as mock_charge:
        result = SubscriptionService.upgrade(db, user, "tok_visa", "Premium")
    mock_charge.assert_not_called()
    assert result["success"] is True
    assert "Premium" in result["message"]


def test_upgrade_success_calls_set_premium():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ) as mock_set:
        mock_charge.return_value = MagicMock(id="ch_test_123")
        result = SubscriptionService.upgrade(db, user, "tok_visa", "Premium")
    mock_charge.assert_called_once()
    mock_set.assert_called_once_with(db, user)
    assert result["success"] is True
    assert result["message"] == "Welcome to Premium! Unlimited uploads unlocked."


def test_upgrade_card_declined_raises_402():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    card_error = stripe.error.CardError(
        message="Your card was declined.",
        param="",
        code="card_declined",
    )
    with patch(
        "app.services.subscription_service.stripe.Charge.create", side_effect=card_error
    ):
        with pytest.raises(HTTPException) as exc_info:
            SubscriptionService.upgrade(db, user, "tok_chargeDeclined", "Premium")
    assert exc_info.value.status_code == 402

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
    assert result["data"]["billing_cycle"] is None


def test_get_subscription_premium_monthly():
    user = make_fake_user(is_premium=True, track_count=5, billing_cycle="monthly")
    result = SubscriptionService.get_subscription(user)
    assert result["data"]["plan"] == "Premium"
    assert result["data"]["limit"] is None
    assert result["data"]["billing_cycle"] == "monthly"


def test_get_subscription_premium_yearly():
    user = make_fake_user(is_premium=True, track_count=10, billing_cycle="yearly")
    result = SubscriptionService.get_subscription(user)
    assert result["data"]["plan"] == "Premium"
    assert result["data"]["limit"] is None
    assert result["data"]["billing_cycle"] == "yearly"


# ── upgrade ─────────────────────────────────────────────────────────────────────


def test_upgrade_invalid_plan_raises_400():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        SubscriptionService.upgrade(db, user, "tok_visa", "Free", "monthly")
    assert exc_info.value.status_code == 400


def test_upgrade_already_premium_is_idempotent():
    user = make_fake_user(is_premium=True)
    db = MagicMock()
    with patch("app.services.subscription_service.stripe.Charge.create") as mock_charge:
        result = SubscriptionService.upgrade(db, user, "tok_visa", "Premium", "monthly")
    mock_charge.assert_not_called()
    assert result["success"] is True
    assert "Premium" in result["message"]


def test_upgrade_monthly_charges_999():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ):
        mock_charge.return_value = MagicMock(id="ch_test_monthly")
        SubscriptionService.upgrade(db, user, "tok_visa", "Premium", "monthly")
    mock_charge.assert_called_once()
    call_kwargs = mock_charge.call_args[1]
    assert call_kwargs["amount"] == 999


def test_upgrade_yearly_charges_9999():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ):
        mock_charge.return_value = MagicMock(id="ch_test_yearly")
        SubscriptionService.upgrade(db, user, "tok_visa", "Premium", "yearly")
    mock_charge.assert_called_once()
    call_kwargs = mock_charge.call_args[1]
    assert call_kwargs["amount"] == 9999


def test_upgrade_monthly_calls_set_premium_with_cycle():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ) as mock_set:
        mock_charge.return_value = MagicMock(id="ch_test_123")
        result = SubscriptionService.upgrade(db, user, "tok_visa", "Premium", "monthly")
    mock_set.assert_called_once_with(db, user, "monthly")
    assert result["success"] is True
    assert result["message"] == "Welcome to Premium! Unlimited uploads unlocked."


def test_upgrade_yearly_calls_set_premium_with_cycle():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ) as mock_set:
        mock_charge.return_value = MagicMock(id="ch_test_456")
        SubscriptionService.upgrade(db, user, "tok_visa", "Premium", "yearly")
    mock_set.assert_called_once_with(db, user, "yearly")


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
            SubscriptionService.upgrade(
                db, user, "tok_chargeDeclined", "Premium", "monthly"
            )
    assert exc_info.value.status_code == 402


def test_upgrade_yearly_card_declined_raises_402():
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
            SubscriptionService.upgrade(
                db, user, "tok_chargeDeclined", "Premium", "yearly"
            )
    assert exc_info.value.status_code == 402

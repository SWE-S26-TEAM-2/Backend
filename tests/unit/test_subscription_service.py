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


def test_get_subscription_standard_monthly():
    user = make_fake_user(
        is_premium=True, track_count=5,
        billing_cycle="monthly", subscription_tier="standard",
    )
    result = SubscriptionService.get_subscription(user)
    assert result["data"]["plan"] == "Premium"
    assert result["data"]["limit"] is None
    assert result["data"]["billing_cycle"] == "monthly"


def test_get_subscription_standard_yearly():
    user = make_fake_user(
        is_premium=True, track_count=8,
        billing_cycle="yearly", subscription_tier="standard",
    )
    result = SubscriptionService.get_subscription(user)
    assert result["data"]["plan"] == "Premium"
    assert result["data"]["billing_cycle"] == "yearly"


def test_get_subscription_pro_monthly():
    user = make_fake_user(
        is_premium=True, track_count=10,
        billing_cycle="monthly", subscription_tier="pro",
    )
    result = SubscriptionService.get_subscription(user)
    assert result["data"]["plan"] == "Pro"
    assert result["data"]["limit"] is None
    assert result["data"]["billing_cycle"] == "monthly"


def test_get_subscription_pro_yearly():
    user = make_fake_user(
        is_premium=True, track_count=20,
        billing_cycle="yearly", subscription_tier="pro",
    )
    result = SubscriptionService.get_subscription(user)
    assert result["data"]["plan"] == "Pro"
    assert result["data"]["billing_cycle"] == "yearly"


# ── upgrade — plan validation ───────────────────────────────────────────────────


def test_upgrade_standard_wrong_plan_raises_400():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        SubscriptionService.upgrade(db, user, "tok_visa", "Pro", "monthly", "standard")
    assert exc.value.status_code == 400


def test_upgrade_pro_wrong_plan_raises_400():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Premium", "monthly", "pro"
        )
    assert exc.value.status_code == 400


# ── upgrade — 409 already subscribed ───────────────────────────────────────────


def test_upgrade_standard_same_cycle_raises_409_no_switching_message():
    user = make_fake_user(
        is_premium=True, billing_cycle="monthly", subscription_tier="standard"
    )
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Premium", "monthly", "standard"
        )
    assert exc.value.status_code == 409
    assert "Switching" not in exc.value.detail


def test_upgrade_standard_different_cycle_raises_409_with_switching_message():
    user = make_fake_user(
        is_premium=True, billing_cycle="monthly", subscription_tier="standard"
    )
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Premium", "yearly", "standard"
        )
    assert exc.value.status_code == 409
    assert "Switching" in exc.value.detail


def test_upgrade_standard_user_tries_pro_raises_409_switching():
    user = make_fake_user(
        is_premium=True, billing_cycle="monthly", subscription_tier="standard"
    )
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Pro", "monthly", "pro"
        )
    assert exc.value.status_code == 409
    assert "Switching" in exc.value.detail


def test_upgrade_pro_same_cycle_raises_409_no_switching_message():
    user = make_fake_user(
        is_premium=True, billing_cycle="yearly", subscription_tier="pro"
    )
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Pro", "yearly", "pro"
        )
    assert exc.value.status_code == 409
    assert "Switching" not in exc.value.detail


def test_upgrade_pro_user_tries_standard_raises_409_switching():
    user = make_fake_user(
        is_premium=True, billing_cycle="monthly", subscription_tier="pro"
    )
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Premium", "monthly", "standard"
        )
    assert exc.value.status_code == 409
    assert "Switching" in exc.value.detail


# ── upgrade — Stripe charges ────────────────────────────────────────────────────


def test_upgrade_standard_monthly_charges_999():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ):
        mock_charge.return_value = MagicMock(id="ch_std_monthly")
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Premium", "monthly", "standard"
        )
    assert mock_charge.call_args[1]["amount"] == 999


def test_upgrade_standard_yearly_charges_9999():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ):
        mock_charge.return_value = MagicMock(id="ch_std_yearly")
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Premium", "yearly", "standard"
        )
    assert mock_charge.call_args[1]["amount"] == 9999


def test_upgrade_pro_monthly_charges_1999():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ):
        mock_charge.return_value = MagicMock(id="ch_pro_monthly")
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Pro", "monthly", "pro"
        )
    assert mock_charge.call_args[1]["amount"] == 1999


def test_upgrade_pro_yearly_charges_14999():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ):
        mock_charge.return_value = MagicMock(id="ch_pro_yearly")
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Pro", "yearly", "pro"
        )
    assert mock_charge.call_args[1]["amount"] == 14999


def test_upgrade_standard_calls_set_premium_with_tier():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ) as mock_set:
        mock_charge.return_value = MagicMock(id="ch_123")
        result = SubscriptionService.upgrade(
            db, user, "tok_visa", "Premium", "monthly", "standard"
        )
    mock_set.assert_called_once_with(db, user, "monthly", "standard")
    assert result["success"] is True


def test_upgrade_pro_calls_set_premium_with_tier():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge, patch(
        "app.services.subscription_service.UserRepository.set_premium"
    ) as mock_set:
        mock_charge.return_value = MagicMock(id="ch_456")
        SubscriptionService.upgrade(
            db, user, "tok_visa", "Pro", "yearly", "pro"
        )
    mock_set.assert_called_once_with(db, user, "yearly", "pro")


# ── upgrade — error handling ────────────────────────────────────────────────────


def test_upgrade_card_declined_raises_402():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    card_error = stripe.error.CardError(
        message="Your card was declined.", param="", code="card_declined",
    )
    with patch(
        "app.services.subscription_service.stripe.Charge.create",
        side_effect=card_error,
    ):
        with pytest.raises(HTTPException) as exc:
            SubscriptionService.upgrade(
                db, user, "tok_chargeDeclined", "Premium", "monthly", "standard"
            )
    assert exc.value.status_code == 402


def test_upgrade_invalid_token_raises_402():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    invalid_error = stripe.error.InvalidRequestError(
        message="No such token.", param="source",
    )
    with patch(
        "app.services.subscription_service.stripe.Charge.create",
        side_effect=invalid_error,
    ):
        with pytest.raises(HTTPException) as exc:
            SubscriptionService.upgrade(
                db, user, "bad_token", "Pro", "monthly", "pro"
            )
    assert exc.value.status_code == 402


def test_upgrade_stripe_auth_error_raises_503():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create",
        side_effect=stripe.error.AuthenticationError("Invalid API key"),
    ):
        with pytest.raises(HTTPException) as exc:
            SubscriptionService.upgrade(
                db, user, "tok_visa", "Premium", "monthly", "standard"
            )
    assert exc.value.status_code == 503


def test_upgrade_stripe_generic_error_raises_502():
    user = make_fake_user(is_premium=False)
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create",
        side_effect=stripe.error.StripeError("Service unavailable"),
    ):
        with pytest.raises(HTTPException) as exc:
            SubscriptionService.upgrade(
                db, user, "tok_visa", "Pro", "yearly", "pro"
            )
    assert exc.value.status_code == 502


def test_upgrade_already_subscribed_does_not_call_stripe():
    user = make_fake_user(
        is_premium=True, billing_cycle="monthly", subscription_tier="standard"
    )
    db = MagicMock()
    with patch(
        "app.services.subscription_service.stripe.Charge.create"
    ) as mock_charge:
        with pytest.raises(HTTPException) as exc:
            SubscriptionService.upgrade(
                db, user, "tok_visa", "Premium", "monthly", "standard"
            )
    mock_charge.assert_not_called()
    assert exc.value.status_code == 409

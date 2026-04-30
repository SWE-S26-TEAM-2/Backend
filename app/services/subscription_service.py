"""
Business logic for the subscription module.

Handles reading subscription status from the User model and upgrading
a user to Standard Premium or Pro via a real Stripe test-mode charge.

Standard Premium — Monthly: $9.99  | Yearly: $99.99
Pro             — Monthly: $19.99 | Yearly: $149.99
"""

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import config
from app.repositories.user_repo import UserRepository

stripe.api_key = config.STRIPE_SECRET_KEY

FREE_TRACK_LIMIT = 3

STANDARD_PRICES = {
    "monthly": 999,    # $9.99
    "yearly": 9999,    # $99.99
}

PRO_PRICES = {
    "monthly": 1999,   # $19.99
    "yearly": 14999,   # $149.99
}

PLAN_NAMES = {
    "standard": "Premium",
    "pro": "Pro",
}

EXPECTED_PLAN = {
    "standard": "Premium",
    "pro": "Pro",
}


class SubscriptionService:
    @staticmethod
    def get_subscription(user) -> dict:
        """
        Return the current user's subscription plan, upload usage, and billing cycle.

        Free users have a limit of 3 uploaded tracks.
        Premium users are Standard or Pro — both get unlimited uploads.

        Args:
            user: The authenticated User ORM object.

        Returns:
            dict: Success envelope with plan, tracks_uploaded, limit,
                  and billing_cycle.
        """
        if user.is_premium:
            tier = getattr(user, "subscription_tier", None)
            plan = "Pro" if tier == "pro" else "Premium"
            limit = None
        else:
            plan = "Free"
            limit = FREE_TRACK_LIMIT

        billing_cycle = getattr(user, "billing_cycle", None)
        return {
            "success": True,
            "data": {
                "plan": plan,
                "tracks_uploaded": user.track_count,
                "limit": limit,
                "billing_cycle": billing_cycle if user.is_premium else None,
            },
        }

    @staticmethod
    def upgrade(
        db: Session,
        user,
        payment_token: str,
        plan: str,
        billing_cycle: str,
        tier: str = "standard",
    ) -> dict:
        """
        Upgrade a user to Standard Premium or Pro via a Stripe charge.

        Already-subscribed users receive a 409 — no Stripe call is made so
        no failed payment is recorded. For free users, tok_visa succeeds and
        any other token is declined by Stripe which records the failure.

        Args:
            db (Session): The database session.
            user: The authenticated User ORM object.
            payment_token (str): A Stripe test token (e.g. tok_visa).
            plan (str): "Premium" for standard tier, "Pro" for pro tier.
            billing_cycle (str): "monthly" or "yearly".
            tier (str): "standard" or "pro", determined by the endpoint called.

        Returns:
            dict: Success message on upgrade.

        Raises:
            HTTPException: 400 if plan does not match the endpoint tier.
            HTTPException: 402 if the card is declined or token is invalid.
            HTTPException: 409 if the user is already subscribed to any plan.
            HTTPException: 503 if the Stripe API key is not configured.
            HTTPException: 502 if Stripe returns an unexpected error.
        """
        expected = EXPECTED_PLAN[tier]
        if plan != expected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan. Must be '{expected}'.",
            )

        if user.is_premium:
            current_tier = (
                getattr(user, "subscription_tier", None) or "standard"
            )
            current_cycle = getattr(user, "billing_cycle", None) or "unknown"
            current_name = PLAN_NAMES.get(current_tier, "Premium")

            if current_tier != tier:
                detail = (
                    f"You are already subscribed to the "
                    f"{current_name} {current_cycle} plan. "
                    f"Switching between plans is not supported."
                )
            elif current_cycle == billing_cycle:
                detail = (
                    f"You are already subscribed to the "
                    f"{current_name} {current_cycle} plan."
                )
            else:
                detail = (
                    f"You are already subscribed to the "
                    f"{current_name} {current_cycle} plan. "
                    f"Switching between plans is not supported."
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )

        prices = PRO_PRICES if tier == "pro" else STANDARD_PRICES
        amount = prices[billing_cycle]

        try:
            stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=payment_token,
                description=(
                    f"Streamline {PLAN_NAMES[tier]} "
                    f"subscription ({billing_cycle})"
                ),
            )
        except (stripe.error.CardError, stripe.error.InvalidRequestError):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Card declined",
            )
        except stripe.error.AuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service is not configured correctly.",
            )
        except stripe.error.StripeError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment service error. Please try again later.",
            )

        UserRepository.set_premium(db, user, billing_cycle, tier)

        return {
            "success": True,
            "message": "Welcome to Premium! Unlimited uploads unlocked.",
        }

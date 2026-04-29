"""
Business logic for the subscription module.

Handles reading subscription status from the User model and upgrading
a user to Premium via a real Stripe test-mode charge.
Monthly plan: $9.99 — Yearly plan: $99.99.
"""

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import config
from app.repositories.user_repo import UserRepository

stripe.api_key = config.STRIPE_SECRET_KEY

FREE_TRACK_LIMIT = 3

PRICES = {
    "monthly": 999,   # $9.99
    "yearly": 9999,   # $99.99
}


class SubscriptionService:
    @staticmethod
    def get_subscription(user) -> dict:
        """
        Return the current user's subscription plan, upload usage, and billing cycle.

        Free users have a limit of 3 uploaded tracks and no billing cycle.
        Premium users are unlimited with a stored billing cycle.

        Args:
            user: The authenticated User ORM object.

        Returns:
            dict: Success envelope with plan, tracks_uploaded, limit, and billing_cycle.
        """
        plan = "Premium" if user.is_premium else "Free"
        limit = None if user.is_premium else FREE_TRACK_LIMIT
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
    def upgrade(db: Session, user, payment_token: str, plan: str,
                billing_cycle: str) -> dict:
        """
        Upgrade a user to Premium by processing a Stripe charge.

        Uses Stripe's test mode — pass a real Stripe test token such as
        tok_visa (success) or tok_chargeDeclined (decline).
        The upgrade is idempotent: calling it on an already-Premium user
        returns success without making another charge.

        Args:
            db (Session): The database session.
            user: The authenticated User ORM object.
            payment_token (str): A Stripe test token (e.g. tok_visa).
            plan (str): Must be "Premium".
            billing_cycle (str): "monthly" or "yearly", set by the endpoint called.

        Returns:
            dict: Success message on upgrade.

        Raises:
            HTTPException: 400 if plan is not "Premium".
            HTTPException: 402 if the Stripe card is declined.
        """
        if plan != "Premium":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan. Must be 'Premium'.",
            )

        if user.is_premium:
            return {
                "success": True,
                "message": "Welcome to Premium! Unlimited uploads unlocked.",
            }

        amount = PRICES[billing_cycle]

        try:
            stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=payment_token,
                description=f"Streamline Premium subscription ({billing_cycle})",
            )
        except stripe.error.CardError:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Card declined",
            )

        UserRepository.set_premium(db, user, billing_cycle)

        return {
            "success": True,
            "message": "Welcome to Premium! Unlimited uploads unlocked.",
        }

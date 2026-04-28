"""
Business logic for the subscription module.

Handles reading subscription status from the User model and upgrading
a user to Premium via a real Stripe test-mode charge.
"""

import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import config
from app.repositories.user_repo import UserRepository

stripe.api_key = config.STRIPE_SECRET_KEY

FREE_TRACK_LIMIT = 3


class SubscriptionService:
    @staticmethod
    def get_subscription(user) -> dict:
        """
        Return the current user's subscription plan and upload usage.

        Free users have a limit of 3 uploaded tracks. Premium users are
        unlimited (limit is None).

        Args:
            user: The authenticated User ORM object.

        Returns:
            dict: Success envelope with plan, tracks_uploaded, and limit.
        """
        plan = "Premium" if user.is_premium else "Free"
        limit = None if user.is_premium else FREE_TRACK_LIMIT
        return {
            "success": True,
            "data": {
                "plan": plan,
                "tracks_uploaded": user.track_count,
                "limit": limit,
            },
        }

    @staticmethod
    def upgrade(db: Session, user, payment_token: str, plan: str) -> dict:
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

        try:
            stripe.Charge.create(
                amount=999,
                currency="usd",
                source=payment_token,
                description="Streamline Premium subscription",
            )
        except stripe.error.CardError:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Card declined",
            )

        UserRepository.set_premium(db, user)

        return {
            "success": True,
            "message": "Welcome to Premium! Unlimited uploads unlocked.",
        }

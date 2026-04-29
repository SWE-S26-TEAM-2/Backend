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

        Already-subscribed users receive a 409 and Stripe is never called,
        so no failed payment is recorded in Stripe.
        For all other users, Stripe processes the token: tok_visa succeeds,
        tok_chargeDeclined and any invalid token are declined and Stripe
        records the failure in the dashboard.

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
            HTTPException: 402 if the card is declined or token is invalid.
            HTTPException: 409 if the user is already subscribed to any plan.
            HTTPException: 503 if the Stripe API key is not configured.
            HTTPException: 502 if Stripe returns an unexpected error.
        """
        if plan != "Premium":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan. Must be 'Premium'.",
            )

        # Check before calling Stripe so no failed charge is recorded
        if user.is_premium:
            current_cycle = getattr(user, "billing_cycle", None) or "unknown"
            if current_cycle == billing_cycle:
                detail = f"You are already subscribed to the {current_cycle} plan."
            else:
                detail = (
                    f"You are already subscribed to the {current_cycle} plan. "
                    f"Switching between plans is not supported."
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )

        amount = PRICES[billing_cycle]

        try:
            stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=payment_token,
                description=f"Streamline Premium subscription ({billing_cycle})",
            )
        except (stripe.error.CardError, stripe.error.InvalidRequestError):
            # Stripe has already recorded the failed attempt in the dashboard
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

        UserRepository.set_premium(db, user, billing_cycle)

        return {
            "success": True,
            "message": "Welcome to Premium! Unlimited uploads unlocked.",
        }

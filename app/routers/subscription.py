"""
Subscription router.

Exposes endpoints for reading a user's subscription status and upgrading
to Premium via Stripe — either monthly ($9.99) or yearly ($99.99).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.schemas.responses import MessageResponse
from app.schemas.subscription_schema import SubscriptionResponse, UpgradeRequest
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/me", response_model=SubscriptionResponse)
def get_subscription(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get the current user's subscription status and upload usage.

    Returns the plan name ("Free" or "Premium"), how many tracks the user
    has uploaded, the upload limit (3 for Free, null for Premium), and
    the billing cycle ("monthly", "yearly", or null for Free users).

    Requires Bearer JWT authentication.
    """
    return SubscriptionService.get_subscription(user)


@router.post("/upgrade/monthly", response_model=MessageResponse)
def upgrade_monthly(
    body: UpgradeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Upgrade the current user to Premium with a monthly billing cycle ($9.99).

    Accepts a Stripe test token and plan="Premium". Charges 999 cents (USD).

    Requires Bearer JWT authentication.
    """
    return SubscriptionService.upgrade(db, user, body.payment_token, body.plan,
                                       "monthly")


@router.post("/upgrade/yearly", response_model=MessageResponse)
def upgrade_yearly(
    body: UpgradeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Upgrade the current user to Premium with a yearly billing cycle ($99.99).

    Accepts a Stripe test token and plan="Premium". Charges 9999 cents (USD).

    Requires Bearer JWT authentication.
    """
    return SubscriptionService.upgrade(db, user, body.payment_token, body.plan,
                                       "yearly")

"""
Subscription router.

Exposes endpoints for reading a user's subscription status and upgrading
to Premium via Stripe.
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
    has uploaded, and the upload limit (3 for Free, null for Premium).

    Requires Bearer JWT authentication.
    """
    return SubscriptionService.get_subscription(user)


@router.post("/upgrade", response_model=MessageResponse)
def upgrade(
    body: UpgradeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Upgrade the current user to Premium via a Stripe charge.

    Accepts a Stripe test token and the target plan ("Premium").
    On success, the user's is_premium flag is set to True permanently.

    Requires Bearer JWT authentication.
    """
    return SubscriptionService.upgrade(db, user, body.payment_token, body.plan)

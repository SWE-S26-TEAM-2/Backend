"""
Subscription router.

Standard Premium — Monthly ($9.99) and Yearly ($99.99).
Pro             — Monthly ($19.99) and Yearly ($149.99).
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

    Returns plan ("Free", "Premium", or "Pro"), billing cycle,
    tracks uploaded, and upload limit.

    Requires Bearer JWT authentication.
    """
    return SubscriptionService.get_subscription(user)


# ── Standard Premium ────────────────────────────────────────────────────────────


@router.post("/upgrade/monthly", response_model=MessageResponse)
def upgrade_monthly(
    body: UpgradeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Upgrade to Standard Premium with monthly billing ($9.99).
    Request body: payment_token and plan="Premium".
    Requires Bearer JWT authentication.
    """
    return SubscriptionService.upgrade(
        db, user, body.payment_token, body.plan, "monthly", "standard"
    )


@router.post("/upgrade/yearly", response_model=MessageResponse)
def upgrade_yearly(
    body: UpgradeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Upgrade to Standard Premium with yearly billing ($99.99).
    Request body: payment_token and plan="Premium".
    Requires Bearer JWT authentication.
    """
    return SubscriptionService.upgrade(
        db, user, body.payment_token, body.plan, "yearly", "standard"
    )


# ── Pro ─────────────────────────────────────────────────────────────────────────


@router.post("/upgrade/pro/monthly", response_model=MessageResponse)
def upgrade_pro_monthly(
    body: UpgradeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Upgrade to Pro with monthly billing ($19.99).
    Request body: payment_token and plan="Pro".
    Requires Bearer JWT authentication.
    """
    return SubscriptionService.upgrade(
        db, user, body.payment_token, body.plan, "monthly", "pro"
    )


@router.post("/upgrade/pro/yearly", response_model=MessageResponse)
def upgrade_pro_yearly(
    body: UpgradeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Upgrade to Pro with yearly billing ($149.99).
    Request body: payment_token and plan="Pro".
    Requires Bearer JWT authentication.
    """
    return SubscriptionService.upgrade(
        db, user, body.payment_token, body.plan, "yearly", "pro"
    )

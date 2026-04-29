"""
Pydantic schemas for the subscription module.

Defines request and response shapes for GET /subscriptions/me,
POST /subscriptions/upgrade/monthly, and POST /subscriptions/upgrade/yearly.
"""

from typing import Optional

from pydantic import BaseModel


class UpgradeRequest(BaseModel):
    """Request body for upgrading to Premium (monthly or yearly endpoint)."""

    payment_token: str
    plan: str


class SubscriptionData(BaseModel):
    """Subscription details returned in GET /subscriptions/me."""

    plan: str
    tracks_uploaded: int
    limit: Optional[int]        # 3 for Free, None for Premium
    billing_cycle: Optional[str]  # "monthly", "yearly", or None for Free


class SubscriptionResponse(BaseModel):
    """Wrapper response for GET /subscriptions/me."""

    success: bool
    data: SubscriptionData

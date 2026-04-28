"""
Pydantic schemas for the subscription module.

Defines request and response shapes for GET /subscriptions/me
and POST /subscriptions/upgrade.
"""

from typing import Optional

from pydantic import BaseModel


class UpgradeRequest(BaseModel):
    """Request body for upgrading to Premium."""

    payment_token: str
    plan: str


class SubscriptionData(BaseModel):
    """Subscription details returned in GET /subscriptions/me."""

    plan: str
    tracks_uploaded: int
    limit: Optional[int]  # None for Premium (unlimited), 3 for Free


class SubscriptionResponse(BaseModel):
    """Wrapper response for GET /subscriptions/me."""

    success: bool
    data: SubscriptionData

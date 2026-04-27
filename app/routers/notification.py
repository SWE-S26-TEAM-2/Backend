from uuid import UUID

from fastapi import APIRouter, Depends, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User  # type: ignore
from app.services.notification_service import NotificationService
from app.schemas.responses import (  # type: ignore
    MessageResponse,
    NotificationsResponse,
    UnreadCountResponse,
    MarkReadResponse,
    MarkAllReadResponse,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationsResponse)
def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationService.get_notifications(
        db, current_user, limit=limit, offset=offset
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationService.get_unread_count(db, current_user)


@router.put("/read-all", response_model=MarkAllReadResponse)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationService.mark_all_as_read(db, current_user)


@router.put("/{notification_id}/read", response_model=MarkReadResponse)
def mark_notification_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationService.mark_as_read(db, current_user, notification_id)


@router.delete("/{notification_id}", response_model=MessageResponse)
def delete_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return NotificationService.delete_notification(db, current_user, notification_id)

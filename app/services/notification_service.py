from uuid import UUID

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.user import User  # type: ignore
from app.repositories.notification_repo import NotificationRepository


class NotificationService:

    @staticmethod
    def get_notifications(
        db: Session,
        current_user: User,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        notifications = NotificationRepository.get_by_user(
            db, current_user.user_id, limit=limit, offset=offset
        )

        return {
            "success": True,
            "data": {
                "notifications": [
                    {
                        "notification_id": str(n.notification_id),
                        "actor_id": str(n.actor_id),
                        "notification_type": n.notification_type,
                        "target_id": (
                            str(n.target_id) if n.target_id else None
                        ),
                        "message": n.message,
                        "is_read": n.is_read,
                        "created_at": n.created_at,
                    }
                    for n in notifications
                ],
            },
        }

    @staticmethod
    def mark_as_read(
        db: Session,
        current_user: User,
        notification_id: UUID,
    ) -> dict:
        notification = NotificationRepository.get_by_id(db, notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found.",
            )

        if str(notification.user_id) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only mark your own notifications as read.",
            )

        if notification.is_read:
            return {
                "success": True,
                "message": "Notification was already marked as read.",
                "data": {
                    "notification_id": str(notification_id),
                    "is_read": True,
                },
            }

        updated = NotificationRepository.mark_as_read(db, notification)

        return {
            "success": True,
            "message": "Notification marked as read.",
            "data": {
                "notification_id": str(updated.notification_id),
                "is_read": updated.is_read,
            },
        }

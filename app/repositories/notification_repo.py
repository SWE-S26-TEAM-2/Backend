from sqlalchemy.orm import Session  # type: ignore

from app.models.notification import Notification  # type: ignore


class NotificationRepository:

    @staticmethod
    def get_by_id(db: Session, notification_id):
        return (
            db.query(Notification)
            .filter(Notification.notification_id == notification_id)
            .first()
        )

    @staticmethod
    def get_by_user(db: Session, user_id, limit: int = 50, offset: int = 0):
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def create(
        db: Session,
        user_id,
        actor_id,
        notification_type: str,
        message: str,
        target_id=None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            actor_id=actor_id,
            notification_type=notification_type,
            message=message,
            target_id=target_id,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_as_read(db: Session, notification: Notification):
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification

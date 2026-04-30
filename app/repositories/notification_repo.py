from sqlalchemy.orm import Session, aliased  # type: ignore

from app.models.notification import Notification  # type: ignore
from app.models.user import User  # type: ignore


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
        Actor = aliased(User)
        return (
            db.query(Notification, Actor.username, Actor.display_name, Actor.profile_picture)
            .join(Actor, Notification.actor_id == Actor.user_id)
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

    @staticmethod
    def get_unread_count(db: Session, user_id) -> int:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .count()
        )

    @staticmethod
    def mark_all_as_read(db: Session, user_id) -> int:
        updated = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .all()
        )
        for n in updated:
            n.is_read = True
        db.commit()
        return len(updated)

    @staticmethod
    def delete(db: Session, notification: Notification) -> None:
        db.delete(notification)
        db.commit()

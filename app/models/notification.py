import uuid

from sqlalchemy import Column, String, Boolean, TIMESTAMP  # type: ignore
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Notification(Base):
    __tablename__ = "notifications"
    __allow_unmapped__ = True

    notification_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_type = Column(
        String(20), nullable=False
    )  # like, comment, repost, follow, message
    target_id = Column(UUID(as_uuid=True), nullable=True)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

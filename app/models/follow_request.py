import uuid

from sqlalchemy import Column, TIMESTAMP, ForeignKey, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database.database import Base


class FollowRequest(Base):
    __tablename__ = "follow_requests"
    __allow_unmapped__ = True

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requester_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    target_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint(
            "requester_id", "target_id", name="uq_follow_request"
        ),
    )

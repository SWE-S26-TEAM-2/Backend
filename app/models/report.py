import uuid

from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, text  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class Report(Base):
    __tablename__ = "reports"
    __allow_unmapped__ = True

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(String(500), nullable=False)
    status = Column(String(20), server_default="open", nullable=False)
    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    resolution_note = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

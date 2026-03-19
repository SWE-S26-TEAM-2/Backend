import uuid

from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP, text  # type: ignore
from sqlalchemy.dialects.postgresql import UUID  # type: ignore

from app.database.database import Base  # type: ignore


class User(Base):
    __tablename__ = "users"
    __allow_unmapped__ = True

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    account_type = Column(String, server_default="listener")
    is_verified = Column(Boolean, server_default="false")
    is_suspended = Column(Boolean, server_default="false")
    CAPTCHA_verified = Column(Boolean, server_default="false")

    bio = Column(String, nullable=True)
    location = Column(String, nullable=True)
    is_premium = Column(Boolean, server_default="false")
    is_private = Column(Boolean, server_default="false")

    profile_picture = Column(String, nullable=True)
    cover_photo = Column(String, nullable=True)

    follower_count = Column(Integer, server_default="0")
    following_count = Column(Integer, server_default="0")
    track_count = Column(Integer, server_default="0")

    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)

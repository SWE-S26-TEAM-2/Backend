from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.database import Base


class SocialLink(Base):
    __tablename__ = "social_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(ForeignKey("users.user_id"), nullable=False)
    platform = Column(String, nullable=False)
    url = Column(String, nullable=False)

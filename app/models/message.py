from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    user = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    public_response = Column(Text)
    dm_response = Column(Text)
    credits_used = Column(Integer, default=0)
    redirected = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now()) 
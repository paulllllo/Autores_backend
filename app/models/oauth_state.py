from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base


class OAuthState(Base):
    __tablename__ = "oauth_states"

    state = Column(String(255), primary_key=True)
    code_verifier = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False)
"""
Legacy User schemas - kept for backward compatibility
New code should use Account schemas from app.schemas.account
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserBase(BaseModel):
    """Legacy - use AccountBase instead"""
    twitter_id: str
    access_token: str
    refresh_token: str
    token_expires_at: datetime


class UserCreate(UserBase):
    """Legacy - use AccountCreate instead"""
    pass


class UserUpdate(BaseModel):
    """Legacy - use AccountStatusUpdate instead"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class UserInDB(UserBase):
    """Legacy - use AccountInDB instead"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 
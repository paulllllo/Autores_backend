from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserBase(BaseModel):
    twitter_id: str
    access_token: str
    refresh_token: str
    token_expires_at: datetime


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class UserInDB(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 
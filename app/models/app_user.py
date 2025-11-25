from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field, EmailStr
from typing import Optional
import uuid


class AppUser(Document):
    """Application user model for username/password authentication"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    
    is_active: bool = True
    is_superuser: bool = False
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "app_users"
        indexes = [
            "username",
            "email",
            "is_active"
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe"
            }
        }


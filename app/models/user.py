from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field
import uuid


class User(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    twitter_id: Indexed(str, unique=True)
    access_token: str
    refresh_token: str
    token_expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        indexes = [
            "twitter_id",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "twitter_id": "1234567890",
                "access_token": "token",
                "refresh_token": "refresh",
                "token_expires_at": "2025-10-29T12:00:00"
            }
        } 
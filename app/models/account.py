from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field
from typing import Optional
import uuid
from app.models.enums import AccountSyncStatus


class Account(Document):
    """
    Twitter account being tracked for mentions
    Renamed from User to avoid confusion with future app authentication
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    twitter_id: Indexed(str, unique=True)
    twitter_username: str  # @handle for display
    display_name: Optional[str] = None  # Full name from Twitter
    profile_image_url: Optional[str] = None  # Twitter profile image
    
    # OAuth tokens
    access_token: str
    refresh_token: str
    token_expires_at: datetime
    
    # Account management
    is_active: bool = True  # Can pause tracking without deleting
    sync_status: str = Field(default=AccountSyncStatus.ACTIVE)  # Use enum for validation
    error_message: Optional[str] = None  # Last error if any
    
    # Tracking metadata
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: Optional[str] = None  # App user ID who added this Twitter account
    last_synced_at: Optional[datetime] = None  # Last successful fetch
    total_mentions_tracked: int = 0  # Counter for mentions
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "accounts"  # Collection name in MongoDB
        indexes = [
            "twitter_id",
            "twitter_username",
            "is_active",
            "sync_status",
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "twitter_id": "1234567890",
                "twitter_username": "elonmusk",
                "display_name": "Elon Musk",
                "is_active": True,
                "sync_status": "active",
                "total_mentions_tracked": 42
            }
        }




from beanie import Document
from datetime import datetime
from typing import Optional
from pydantic import Field, BaseModel
import uuid
from app.models.enums import MessageStatus


class TwitterUser(BaseModel):
    """Embedded document for Twitter user info (sender)"""
    twitter_id: str
    username: str  # @handle
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None


class TrackedAccount(BaseModel):
    """Embedded document for tracked account info (recipient)"""
    account_id: str  # Reference to Account document
    twitter_id: str
    username: str  # @handle
    display_name: Optional[str] = None


class Message(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tweet_id: str  # Twitter's tweet ID (same as id, but explicit)
    timestamp: datetime
    text: str
    
    # Sender information (who mentioned the account)
    sender: TwitterUser
    
    # Account information (which tracked account received this mention)
    sent_to: TrackedAccount
    
    # Legacy field for backward compatibility (kept for migration)
    user: Optional[str] = None  # Old twitter user ID field
    
    # Processing status
    status: str = Field(default=MessageStatus.PENDING)
    public_response: Optional[str] = None
    dm_response: Optional[str] = None
    credits_used: int = 0
    redirected: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "messages"
        indexes = [
            "timestamp",
            "tweet_id",
            "sender.twitter_id",
            "sent_to.account_id",
            "sent_to.twitter_id",
            "status",
            "user",  # Keep for backward compatibility
        ] 
from beanie import Document
from datetime import datetime
from typing import Optional
from pydantic import Field
import uuid


class Message(Document):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    user: str  # Twitter user ID
    text: str
    status: str = "pending"
    public_response: Optional[str] = None
    dm_response: Optional[str] = None
    credits_used: int = 0
    redirected: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "messages"
        indexes = [
            "timestamp",
            "user",
            "status",
        ] 
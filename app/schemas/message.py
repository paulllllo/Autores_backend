from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.enums import MessageStatus
# Import the embedded models from the Message model to avoid duplication
from app.models.message import TwitterUser, TrackedAccount


# Keep these aliases for backward compatibility
TwitterUserInfo = TwitterUser
TrackedAccountInfo = TrackedAccount


class MessageBase(BaseModel):
    id: str
    tweet_id: str
    timestamp: datetime
    text: str
    sender: TwitterUser  # Who sent the mention
    sent_to: TrackedAccount  # Which account received it
    status: MessageStatus  # Enum for status
    public_response: Optional[str] = None
    dm_response: Optional[str] = None
    credits_used: int = 0
    redirected: bool = False


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    status: Optional[MessageStatus] = None
    public_response: Optional[str] = None
    dm_response: Optional[str] = None
    credits_used: Optional[int] = None
    redirected: Optional[bool] = None


class MessageInDB(MessageBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True  # Serialize enum as string


class FetchMessagesResponse(BaseModel):
    message: str
    new_messages_count: int
    messages: List[MessageInDB]


class GenerateResponseRequest(BaseModel):
    custom_prompt: Optional[str] = None


class GenerateResponseResponse(BaseModel):
    message_id: str
    original_message: str
    generated_response: str
    custom_prompt_used: bool 
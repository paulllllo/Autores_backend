from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class MessageBase(BaseModel):
    id: str
    timestamp: datetime
    user: str
    text: str
    status: str = "pending"
    public_response: Optional[str] = None
    dm_response: Optional[str] = None
    credits_used: int = 0
    redirected: bool = False


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    status: Optional[str] = None
    public_response: Optional[str] = None
    dm_response: Optional[str] = None
    credits_used: Optional[int] = None
    redirected: Optional[bool] = None


class MessageInDB(MessageBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
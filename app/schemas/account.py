from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.enums import AccountSyncStatus


class AccountBase(BaseModel):
    """Base account schema"""
    twitter_id: str
    twitter_username: str
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: bool = True


class AccountCreate(BaseModel):
    """Schema for creating an account (via OAuth)"""
    # No fields needed - populated from OAuth flow
    pass


class AccountInDB(AccountBase):
    """Account schema as stored in database"""
    id: str
    added_at: datetime
    last_synced_at: Optional[datetime] = None
    sync_status: AccountSyncStatus  # Enum for OpenAPI
    error_message: Optional[str] = None
    token_expires_at: datetime
    total_mentions_tracked: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True  # Serialize enum as string value


class AccountSummary(BaseModel):
    """Lightweight account info for listings"""
    id: str
    twitter_username: str
    display_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: bool
    sync_status: AccountSyncStatus
    total_mentions_tracked: int
    last_synced_at: Optional[datetime] = None


class AccountList(BaseModel):
    """Response schema for listing accounts"""
    accounts: list[AccountSummary]
    total: int
    active_count: int
    paused_count: int


class AccountStatusUpdate(BaseModel):
    """Schema for updating account status"""
    is_active: Optional[bool] = Field(None, description="Enable or disable tracking")
    sync_status: Optional[AccountSyncStatus] = Field(None, description="Sync status")


class ReauthorizeResponse(BaseModel):
    """Response when requesting account reauthorization"""
    authorization_url: str
    account_username: str
    message: str




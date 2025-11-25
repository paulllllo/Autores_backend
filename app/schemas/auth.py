from pydantic import BaseModel, HttpUrl
from typing import Optional


class TwitterAuthorizationResponse(BaseModel):
    """Response from initiating Twitter OAuth flow"""
    authorization_url: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "authorization_url": "https://twitter.com/i/oauth2/authorize?response_type=code&client_id=...",
                "message": "Redirect user to this URL to authorize their Twitter account"
            }
        }


class TwitterCallbackResponse(BaseModel):
    """Response from Twitter OAuth callback"""
    message: str
    account: "TwitterAccountInfo"
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Successfully added Twitter account @elonmusk for tracking",
                "account": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "twitter_id": "1234567890",
                    "twitter_username": "elonmusk",
                    "display_name": "Elon Musk",
                    "is_active": True
                }
            }
        }


class TwitterAccountInfo(BaseModel):
    """Basic Twitter account information"""
    id: str
    twitter_id: str
    twitter_username: str
    display_name: Optional[str] = None
    is_active: bool


class TokenRefreshResponse(BaseModel):
    """Response from token refresh"""
    message: str
    expires_at: str
    account_username: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Successfully refreshed token",
                "expires_at": "2024-12-01T12:00:00",
                "account_username": "elonmusk"
            }
        }


# Update forward references
TwitterCallbackResponse.model_rebuild()

